import QtQuick

Rectangle {
    id: root
    gradient: Gradient {
        GradientStop { position: 0; color: "#111c2a" }
        GradientStop { position: 0.54; color: "#0c111a" }
        GradientStop { position: 1; color: "#070a10" }
    }
    // KSplashQML writes this property as the session progresses.
    property int stage: 0
    property bool reducedMotion: false
    Column {
        anchors.centerIn: parent
        spacing: 28
        Image {
            anchors.horizontalCenter: parent.horizontalCenter
            source: "file:///usr/share/onyx-os/boot-logo.png"
            sourceSize.width: 240
            width: 240
            height: 120
            fillMode: Image.PreserveAspectFit
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Obryx OS 0.4"
            color: "#c7d7e6"
            font.pixelSize: 16
            font.letterSpacing: 4
        }
        Grid {
            anchors.horizontalCenter: parent.horizontalCenter
            columns: 3
            spacing: 6
            Repeater {
                model: 9
                Rectangle {
                    id: square
                    required property int index
                    width: 10
                    height: 10
                    radius: 2
                    color: "#b8e1ee"
                    opacity: root.reducedMotion ? 0.7 : 0.2
                    SequentialAnimation on opacity {
                        running: !root.reducedMotion && root.stage < 6
                        loops: Animation.Infinite
                        PauseAnimation { duration: square.index * 80 }
                        NumberAnimation { to: 1; duration: 220 }
                        NumberAnimation { to: 0.2; duration: 400 }
                        PauseAnimation { duration: (8 - square.index) * 80 }
                    }
                }
            }
        }
    }
}
