import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as Support

PlasmoidItem {
    id: home
    preferredRepresentation: fullRepresentation
    toolTipMainText: "ONYX Home"
    function openHome() { runner.connectSource("gtk-launch onyx-home") }
    Connections {
        target: Plasmoid
        function onActivated() { home.openHome() }
    }
    Support.DataSource {
        id: runner
        engine: "executable"
        onNewData: function(source, data) { disconnectSource(source) }
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
