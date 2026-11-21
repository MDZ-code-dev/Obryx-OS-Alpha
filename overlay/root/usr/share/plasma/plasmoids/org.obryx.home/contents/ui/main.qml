import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root
    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    Plasmoid.onActivated: root.openHome()
    function openHome() {
        runner.connectSource("/usr/bin/python3 /usr/share/onyx-os/shell.py home >/dev/null 2>&1 &")
    }
    P5Support.DataSource {
        id: runner
        engine: "executable"
        connectedSources: []
        onNewData: (sourceName, data) => disconnectSource(sourceName)
    }
    fullRepresentation: MouseArea {
        implicitWidth: 56
        implicitHeight: 56
        Layout.minimumWidth: 48
        Layout.minimumHeight: 48
        hoverEnabled: true
        activeFocusOnTab: true
        Accessible.name: "Obryx Home"
        Accessible.role: Accessible.Button
        onClicked: root.openHome()
        Keys.onReturnPressed: root.openHome()
        Keys.onSpacePressed: root.openHome()
        Kirigami.Icon {
            anchors.centerIn: parent
            width: 36
            height: 42
            source: "onyx-crystal"
            active: parent.containsMouse
            scale: parent.pressed ? 0.92 : (parent.containsMouse ? 1.08 : 1)
            Behavior on scale { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
        }
    }
}
