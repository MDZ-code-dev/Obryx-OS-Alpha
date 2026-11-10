import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    property alias cfg_iconSpacing:       spacingBox.value
    property alias cfg_iconSize:          iconSizeBox.value
    property alias cfg_cornerRadius:      cornerRadiusBox.value
    property alias cfg_paddingHorizontal: paddingHBox.value
    property alias cfg_paddingVertical:   paddingVBox.value
    property alias cfg_hoverLift:         hoverLiftBox.value

    // Doubles — can't alias to int SpinBox directly
    property real cfg_hoverScale:        1.4
    property real cfg_backgroundOpacity: 0.88

    Kirigami.FormLayout {

        // ── Layout ────────────────────────────────────────────────────────────
        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Kirigami.FormData.label: i18n("Layout")
        }

        QQC2.SpinBox {
            id: spacingBox
            Kirigami.FormData.label: i18n("App spacing (px):")
            from: 0
            to: 48
        }

        QQC2.SpinBox {
            id: iconSizeBox
            Kirigami.FormData.label: i18n("Icon size (px):")
            from: 24
            to: 128
        }

        QQC2.SpinBox {
            id: paddingHBox
            Kirigami.FormData.label: i18n("Horizontal padding (px):")
            from: 0
            to: 48
        }

        QQC2.SpinBox {
            id: paddingVBox
            Kirigami.FormData.label: i18n("Vertical padding (px):")
            from: 0
            to: 48
        }

        QQC2.SpinBox {
            id: cornerRadiusBox
            Kirigami.FormData.label: i18n("Corner radius (px):")
            from: 0
            to: 64
        }

        // ── Appearance ────────────────────────────────────────────────────────
        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Kirigami.FormData.label: i18n("Appearance")
        }

        QQC2.Slider {
            id: opacitySlider
            Kirigami.FormData.label: i18n("Background opacity:")
            from:     0.0
            to:       1.0
            stepSize: 0.05
            value:    cfg_backgroundOpacity
            onMoved:  cfg_backgroundOpacity = value

            QQC2.ToolTip {
                visible: opacitySlider.pressed
                text:    Math.round(opacitySlider.value * 100) + "%"
            }
        }

        // ── Behaviour ─────────────────────────────────────────────────────────
        Kirigami.Separator {
            Kirigami.FormData.isSection: true
            Kirigami.FormData.label: i18n("Behaviour")
        }

        QQC2.SpinBox {
            id: hoverScaleBox
            Kirigami.FormData.label: i18n("Hover magnification (%):")
            from:     100
            to:       250
            stepSize: 5
            value:    Math.round(cfg_hoverScale * 100)
            onValueModified: cfg_hoverScale = value / 100.0
        }

        QQC2.SpinBox {
            id: hoverLiftBox
            Kirigami.FormData.label: i18n("Hover lift (px):")
            from:     0
            to:       60
            stepSize: 1
        }
    }
}
