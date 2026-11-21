import QtQuick
import QtQuick.Layouts
import QtQuick.Dialogs
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager

PlasmoidItem {
    id: root

    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation

    readonly property int  iconSize:          Plasmoid.configuration.iconSize
    readonly property int  iconSpacing:       Plasmoid.configuration.iconSpacing
    readonly property int  cornerRadius:      Plasmoid.configuration.cornerRadius
    readonly property int  paddingH:          Plasmoid.configuration.paddingHorizontal
    readonly property int  paddingV:          Plasmoid.configuration.paddingVertical
    readonly property real hoverScale:        Plasmoid.configuration.hoverScale
    readonly property real backgroundOpacity: Plasmoid.configuration.backgroundOpacity
    readonly property int  hoverLift:         Plasmoid.configuration.hoverLift

    property int hoveredIndex: -1
    property real hoverPosition: -1

    Timer {
        id: hoverClearDelay
        interval: 60
        repeat:   false
        onTriggered: root.hoveredIndex = -1
    }

    // ── Launcher management ───────────────────────────────────────────────────
    function removeLauncher(url) {
        const list = Plasmoid.configuration.pinnedLaunchers
            .filter(l => l.toString() !== url.toString())
        Plasmoid.configuration.pinnedLaunchers = list
    }

    // Convert file:///usr/share/applications/foo.desktop → applications:foo.desktop
    // so TasksModel can match a running window to its launcher and group them correctly.
    // Without this, the window appears as a separate unmatched task at the last index.
    function normalizeLauncherUrl(str) {
        const m = str.match(/\/([^/]+\.desktop)$/)
        return m ? "applications:" + m[1] : str
    }

    function addLauncher(url) {
        const str  = root.normalizeLauncherUrl(url.toString())
        const list = Plasmoid.configuration.pinnedLaunchers
        if (!list.some(l => l.toString() === str))
            Plasmoid.configuration.pinnedLaunchers = [...list, str]
    }

    // One-time migration: rewrite any pre-existing file:// launchers in config to
    // the applications: scheme so TasksModel can group their windows correctly.
    function migrateLauncherUrls() {
        const list = Plasmoid.configuration.pinnedLaunchers
        let changed = false
        const out = list.map(u => {
            const s = u.toString()
            const n = root.normalizeLauncherUrl(s)
            if (n !== s) changed = true
            return n
        })
        if (changed) Plasmoid.configuration.pinnedLaunchers = out
    }

    Component.onCompleted: migrateLauncherUrls()

    // Moves item at 'from' to 'to': visual update via model + config save for persistence
    function reorderLaunchers(from, to) {
        if (from === to || from < 0 || to < 0) return

        // 1. Reorder inside the model (SortManual exposes this API)
        tasksModel.move(from, to)

        // 2. syncLaunchers() updates the model's internal launcherList to reflect
        //    the new order — without this, the move() is purely visual and the
        //    persisted launcherList stays out of sync.
        tasksModel.syncLaunchers()

        // 3. Save the now-synced order to config
        Qt.callLater(() => {
            Plasmoid.configuration.pinnedLaunchers = tasksModel.launcherList
        })
    }

    // ── Drag-reorder state ────────────────────────────────────────────────────
    property bool dragActive:     false
    property int  dragFromIndex:  -1
    property int  dragToIndex:    -1
    property real dragGhostX:     0
    property var  dragDecoration: null

    // tasksModel is defined at root level — always in scope, same count as icons shown
    readonly property int iconCount: tasksModel.count

    // File picker
    FileDialog {
        id: addAppDialog
        title:         "Add application to dock"
        currentFolder: "file:///usr/share/applications"
        nameFilters:   ["Applications (*.desktop)", "All files (*)"]
        onAccepted:    root.addLauncher(selectedFile)
    }

    // ONYX manages the complete panel, including Home and the system tray.

    // ── Task model ────────────────────────────────────────────────────────────
    TaskManager.VirtualDesktopInfo { id: virtualDesktopInfo }
    TaskManager.ActivityInfo      { id: activityInfo }

    TaskManager.TasksModel {
        id: tasksModel
        sortMode:  TaskManager.TasksModel.SortManual
        groupMode: TaskManager.TasksModel.GroupApplications
        // When true, a running window adopts the sort position of its launcher
        // instead of being appended at the end. Default is false — without this
        // an app jumps to the last index when opened.
        launchInPlace:    true
        // separateLaunchers=false also implicitly enables launch-in-place behaviour
        // and lets launcher/window groups occupy a single slot under SortManual.
        separateLaunchers: false
        virtualDesktop: virtualDesktopInfo.currentDesktop
        activity:       activityInfo.currentActivity
        filterByVirtualDesktop: true
        filterByActivity:       true
        filterMinimized:        false
        launcherList: Plasmoid.configuration.pinnedLaunchers
    }

    // ── Dock UI ───────────────────────────────────────────────────────────────
    fullRepresentation: Item {
        id: dock

        Layout.preferredWidth:  iconRow.implicitWidth  + 2 * root.paddingH
        Layout.fillHeight: true
        Layout.minimumHeight: Math.ceil(root.iconSize * root.hoverScale) + root.hoverLift + 4
        Layout.preferredHeight: Layout.minimumHeight
        implicitWidth:  Layout.preferredWidth
        implicitHeight: Layout.preferredHeight

        Rectangle {
            anchors.fill: parent
            radius:       root.cornerRadius
            color:        Qt.rgba(0x1c / 255, 0x1e / 255, 0x24 / 255, root.backgroundOpacity)
            antialiasing: true
        }

        RowLayout {
            id: iconRow
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 4
            spacing: root.iconSpacing

            Repeater {
                model: tasksModel
                delegate: TaskIcon {
                    id: iconDelegate
                    taskModel:     tasksModel
                    taskIndex:     index
                    baseSize:      root.iconSize
                    maxScale:      root.hoverScale
                    hoverLift:     root.hoverLift
                    hoveredIndex:  root.hoveredIndex
                    hoverPosition: root.hoverPosition
                    launcherUrl:   model.LauncherUrl ?? ""

                    decoration:    model.decoration
                    isLauncher:    model.IsLauncher    ?? false
                    isWindow:      model.IsWindow      ?? false
                    isActive:      model.IsActive      ?? false
                    isMinimized:   model.IsMinimized   ?? false
                    isGroupParent: model.IsGroupParent ?? false
                    appName:       model.AppName || model.display || ""

                    // Dim the slot while this icon is being dragged out of it
                    opacity: root.dragActive && root.dragFromIndex === index ? 0.2 : 1.0

                    onHoverEntered:  { hoverClearDelay.stop(); root.hoveredIndex = index; root.hoverPosition = index }
                    onHoverExited:   hoverClearDelay.restart()
                    onHoverMoved: function(localX) {
                        hoverClearDelay.stop()
                        root.hoveredIndex = index
                        root.hoverPosition = index + (localX - width / 2) / (root.iconSize + root.iconSpacing)
                    }

                    onRemoveRequested: function(url) { root.removeLauncher(url) }

                    onReorderStarted: {
                        console.log("[DOCK] onReorderStarted index=" + index + " delegateX=" + x
                            + " iconCount=" + root.iconCount
                            + " iconSize=" + root.iconSize + " slot=" + (root.iconSize + root.iconSpacing))
                        root.dragActive     = true
                        root.dragFromIndex  = index
                        root.dragToIndex    = index
                        root.dragDecoration = decoration
                    }
                    // Old-style handler — signal param 'mouseLocalX' auto-injected.
                    // Use root.* instead of local ids (iconRow, iconRepeater) which
                    // are not reliably in scope inside a delegate signal handler.
                    onReorderMoved: {
                        const iconRowX = x + mouseLocalX
                        // iconRow.x == root.paddingH when dock fits its content
                        root.dragGhostX = root.paddingH + iconRowX
                        const slot = root.iconSize + root.iconSpacing
                        let di = Math.round((iconRowX - root.iconSize * 0.5) / slot)
                        di = Math.max(0, Math.min(root.iconCount - 1, di))
                        console.log("[DOCK] onReorderMoved => iconRowX=" + iconRowX.toFixed(1) + " di=" + di)
                        root.dragToIndex = di
                    }
                    onReorderEnded: {
                        console.log("[DOCK] onReorderEnded from=" + root.dragFromIndex + " to=" + root.dragToIndex)
                        root.reorderLaunchers(root.dragFromIndex, root.dragToIndex)
                        root.dragActive    = false
                        root.dragFromIndex = -1
                        root.dragToIndex   = -1
                    }
                }
            }

            // ── Settings gear + Add-launcher buttons ──────────────────────────
            Item {
                readonly property int btnSize: Math.round(root.iconSize * 0.44)
                implicitWidth:  Math.round(root.iconSize * 0.55)
                implicitHeight: root.iconSize

                // Gear icon — top half
                Kirigami.Icon {
                    anchors {
                        top:              parent.top
                        horizontalCenter: parent.horizontalCenter
                    }
                    width:  parent.btnSize
                    height: parent.btnSize
                    source:  "configure"
                    opacity: settingsBtn.containsMouse ? 1.0 : 0.45
                    Behavior on opacity { NumberAnimation { duration: 120 } }
                }

                MouseArea {
                    id: settingsBtn
                    anchors.top:              parent.top
                    anchors.horizontalCenter: parent.horizontalCenter
                    width:  parent.btnSize
                    height: parent.btnSize
                    hoverEnabled: true
                    cursorShape:  Qt.PointingHandCursor
                    onClicked: {
                        // Emit configureRequested on the panel containment,
                        // passing our applet — Plasma 6 native way to open the configure dialog
                        Plasmoid.containment.configureRequested(Plasmoid)
                    }
                }

                // Add-launcher icon — bottom half
                Kirigami.Icon {
                    anchors {
                        bottom:           parent.bottom
                        horizontalCenter: parent.horizontalCenter
                    }
                    width:  parent.btnSize
                    height: parent.btnSize
                    source:  "list-add"
                    opacity: addBtn.containsMouse ? 1.0 : 0.45
                    Behavior on opacity { NumberAnimation { duration: 120 } }
                }

                MouseArea {
                    id: addBtn
                    anchors.bottom:           parent.bottom
                    anchors.horizontalCenter: parent.horizontalCenter
                    width:  parent.btnSize
                    height: parent.btnSize
                    hoverEnabled: true
                    cursorShape:  Qt.PointingHandCursor
                    onClicked:    addAppDialog.open()
                }


            }
        }

        // ── Drag ghost — floating icon that follows the mouse ─────────────────
        Kirigami.Icon {
            visible: root.dragActive
            x:       root.dragGhostX - width / 2
            y:       (dock.height - height) / 2
            width:   root.iconSize
            height:  root.iconSize
            source:  root.dragDecoration
            opacity: 0.75
            z:       10
        }

        // ── Drop indicator — vertical bar, position driven by dragToIndex ────────
        Rectangle {
            id: dropBar
            visible: root.dragActive
            x:      root.paddingH + Math.max(0, root.dragToIndex) * (root.iconSize + root.iconSpacing) - width / 2
            y:      (dock.height - height) / 2
            width:  3
            height: root.iconSize * 0.9
            radius: 1
            color:  "#ffffff"
            opacity: 0.9
            z:      10
        }
    }
}
