import QtQuick 2.15
import QtQuick.Window 2.15

Rectangle {
    id: root
    width: Screen.width
    height: Screen.height
    color: "#0c1017"
    property int pulse: 0
    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: -55
        text: "◆"
        font.pixelSize: 84
        color: "#79d8e9"
        opacity: 0.95
    }
    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: 28
        text: "ONYX OS"
        color: "#f3f7fb"
        font.pixelSize: 34
        font.bold: true
        font.letterSpacing: 5
    }
    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: 98
        spacing: 8
        Repeater {
            model: 9
            Rectangle {
                width: 7; height: 7; radius: 2
                color: "#79d8e9"
                opacity: (index === root.pulse % 9) ? 1 : 0.2
            }
        }
    }
    Timer {
        interval: 140
        repeat: true
        running: true
        onTriggered: root.pulse++
    }
    Connections {
        target: typeof splash !== "undefined" ? splash : null
        function onStageChanged() {
            if (splash.stage >= 5) splash.visible = false
        }
    }
}
