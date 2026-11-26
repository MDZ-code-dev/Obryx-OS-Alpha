import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

Item {
    id: taskIcon

    property var    taskModel:     null
    property int    taskIndex:     0
    property int    baseSize:      48
    property real   maxScale:      1.4
    property int    hoverLift:     0
    property int    hoveredIndex:  -1
    property string launcherUrl:   ""

    property var    decoration:    null
    property bool   isLauncher:    false
    property bool   isWindow:      false
    property bool   isActive:      false
    property bool   isMinimized:   false
    property bool   isGroupParent: false
    property string appName:       ""

    signal hoverEntered()
    signal hoverExited()
    signal removeRequested(string url)
    signal reorderStarted()
    signal reorderMoved(real mouseLocalX)
    signal reorderEnded()

    implicitWidth:  baseSize
    implicitHeight: baseSize

    // ── Magnification ─────────────────────────────────────────────────────────
    readonly property real magnification: {
        if (hoveredIndex < 0) return 0
        const d = Math.abs(taskIndex - hoveredIndex)
        if (d >= 2.5) return 0
        return 0.5 * (1.0 + Math.cos(Math.PI * d / 2.5))
    }

    readonly property real iconTarget: baseSize * (1.0 + (maxScale - 1.0) * magnification)
    property real iconDrawSize: baseSize
    onIconTargetChanged: iconDrawSize = iconTarget
    Behavior on iconDrawSize { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }

    // ── Drag state: 0=idle, 1=horiz(reorder), 2=vert(remove) ─────────────────
    property int  dragMode:  0
    property real pressedX:  0
    property real pressedY:  0

    opacity: dragMode === 2 ? 0.4 : 1.0
    Behavior on opacity { NumberAnimation { duration: 120 } }

    // ── App icon ──────────────────────────────────────────────────────────────
    Kirigami.Icon {
        // Lift the icon proportional to its magnification — hovered icons rise
        // by hoverLift px, neighbours rise less, far icons not at all.
        anchors {
            bottom:           parent.bottom
            bottomMargin:     3 + Math.round(taskIcon.hoverLift * taskIcon.magnification)
            horizontalCenter: parent.horizontalCenter
        }
        Behavior on anchors.bottomMargin { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
        width:  taskIcon.iconDrawSize
        height: taskIcon.iconDrawSize
        source: taskIcon.decoration
        smooth: true; antialiasing: true
        opacity: taskIcon.isMinimized ? 0.55 : 1.0
        Behavior on opacity { NumberAnimation { duration: 120 } }
    }

    // Trash icon during remove-drag
    Kirigami.Icon {
        anchors.centerIn: parent
        width:  taskIcon.baseSize * 0.5
        height: taskIcon.baseSize * 0.5
        source: "user-trash-symbolic"
        visible: taskIcon.dragMode === 2
    }

    // ── Running dot ───────────────────────────────────────────────────────────
    Rectangle {
        anchors { bottom: parent.bottom; horizontalCenter: parent.horizontalCenter; bottomMargin: 1 }
        width: 4; height: 4; radius: 2
        visible: taskIcon.isWindow && !taskIcon.isLauncher
        color:   taskIcon.isActive ? "#ffffff" : "#60626e"
        Behavior on color { ColorAnimation { duration: 120 } }
    }

    QQC2.ToolTip.visible: mouseArea.containsMouse && taskIcon.dragMode === 0 && taskIcon.appName !== ""
    QQC2.ToolTip.text:    taskIcon.appName
    QQC2.ToolTip.delay:   700

    // ── Mouse ─────────────────────────────────────────────────────────────────
    MouseArea {
        id: mouseArea
        anchors.fill:    parent
        hoverEnabled:    true
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onEntered: taskIcon.hoverEntered()
        onExited:  { taskIcon.hoverExited(); if (taskIcon.dragMode === 2) taskIcon.dragMode = 0 }

        onPressed: function(mouse) {
            taskIcon.pressedX = mouse.x
            taskIcon.pressedY = mouse.y
            taskIcon.dragMode = 0
        }

        onPositionChanged: function(mouse) {
            if (!pressed) return
            const dx = mouse.x - taskIcon.pressedX
            const dy = taskIcon.pressedY - mouse.y  // positive = upward

            if (taskIcon.dragMode === 0) {
                if (Math.abs(dx) >= 10 && Math.abs(dx) > Math.abs(dy) * 1.5) {
                    taskIcon.dragMode = 1
                    console.log("[DOCK] reorderStarted: taskIndex=" + taskIcon.taskIndex
                        + " taskIcon.x=" + taskIcon.x + " appName=" + taskIcon.appName)
                    taskIcon.reorderStarted()
                } else if (dy > 40) {
                    taskIcon.dragMode = 2
                }
            }

            if (taskIcon.dragMode === 1) {
                console.log("[DOCK] reorderMoved: taskIndex=" + taskIcon.taskIndex
                    + " taskIcon.x=" + taskIcon.x
                    + " mouse.x=" + mouse.x
                    + " => iconRowX=" + (taskIcon.x + mouse.x))
                taskIcon.reorderMoved(mouse.x)
            } else if (taskIcon.dragMode === 2) {
                if (dy < 30) taskIcon.dragMode = 0   // moved back → cancel
            }
        }

        onReleased: function(mouse) {
            const mode = taskIcon.dragMode
            taskIcon.dragMode = 0

            if (mode === 2 && taskIcon.launcherUrl !== "") {
                taskIcon.removeRequested(taskIcon.launcherUrl)
                return
            }
            if (mode === 1) {
                taskIcon.reorderEnded()
                return
            }

            // Click — ignore if moved much
            const dx = Math.abs(mouse.x - taskIcon.pressedX)
            const dy = Math.abs(taskIcon.pressedY - mouse.y)
            if (dx > 8 || dy > 8) return
            if (mouse.button !== Qt.LeftButton) return
            if (!taskIcon.taskModel) return

            const idx = taskIcon.taskModel.index(taskIcon.taskIndex, 0)
            if (!taskIcon.isWindow || taskIcon.isLauncher)
                taskIcon.taskModel.requestNewInstance(idx)
            else if (taskIcon.isGroupParent)
                taskIcon.taskModel.requestActivate(idx)
            else if (taskIcon.isActive && !taskIcon.isMinimized)
                taskIcon.taskModel.requestToggleMinimized(idx)
            else
                taskIcon.taskModel.requestActivate(idx)
        }
    }
}
