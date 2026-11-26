import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.taskmanager as TaskManager

PlasmoidItem {
    id: home
    preferredRepresentation: fullRepresentation
    toolTipMainText: "ONYX Home"
    function openHome() {
        const row = launchers.launcherPosition("applications:onyx-home.desktop")
        if (row >= 0) launchers.requestNewInstance(launchers.index(row, 0))
    }
    Connections {
        target: Plasmoid
        function onActivated() { home.openHome() }
    }
    TaskManager.TasksModel {
        id: launchers
        launcherList: ["applications:onyx-home.desktop"]
        separateLaunchers: true
        hideActivatedLaunchers: false
        sortMode: TaskManager.TasksModel.SortManual
    }
    fullRepresentation: Item {
        Layout.minimumWidth: 42
        Layout.minimumHeight: 32
        Accessible.role: Accessible.Button
        Accessible.name: "ONYX Home"
        Accessible.onPressAction: home.openHome()
        Image {
            anchors.centerIn: parent
            height: Math.min(parent.height * 0.72, 34)
            scale: pointer.hovered ? 1.18 : 1
            Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
            width: height
            source: "file:///usr/share/onyx-os/crystal.svg"
            fillMode: Image.PreserveAspectFit
        }
        TapHandler { onTapped: home.openHome() }
        HoverHandler { id: pointer; cursorShape: Qt.PointingHandCursor }
    }
}
