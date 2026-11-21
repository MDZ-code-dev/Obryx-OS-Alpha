// Plasma 6 scripting API. A failed replacement preserves the existing panels.
(function () {
    var previous = panels();
    var dock = null;
    var launcher = null;
    for (var i = 0; i < previous.length; ++i) {
        previous[i].currentConfigGroup = ["ONYX"];
        if (previous[i].readConfig("layoutVersion", "") === "0.4.0-obryx") {
            print("ONYX_LAYOUT_OK");
            return;
        }
    }
    try {
        dock = new Panel();
        dock.location = "bottom";
        dock.height = 88;
        dock.floating = true;
        dock.alignment = "center";
        dock.lengthMode = "fit";
        dock.hiding = "none";
        dock.opacity = "translucent";
        var types = ["org.obryx.home", "per.nonobeam.paneldock",
                     "org.kde.plasma.systemtray", "org.kde.plasma.digitalclock"];
        for (var j = 0; j < types.length; ++j) {
            var widget = dock.addWidget(types[j]);
            if (!widget || widget.type !== types[j]) {
                throw new Error("Cannot create required widget: " + types[j]);
            }
            if (j === 0) {
                launcher = widget;
                launcher.currentConfigGroup = [];
                launcher.writeConfig("url", "file:///usr/share/applications/onyx-home.desktop");
            }
            if (j === 3) {
                widget.currentConfigGroup = ["Appearance"];
                widget.writeConfig("showDate", false);
                widget.writeConfig("use24hFormat", 2);
                widget.writeConfig("fontSize", 11);
                widget.writeConfig("autoFontAndSize", false);
            }
            if (j === 1) {
                widget.currentConfigGroup = ["General"];
                widget.writeConfig("iconSize", 38);
                widget.writeConfig("hoverScale", 1.6);
                widget.writeConfig("hoverLift", 7);
                widget.writeConfig("backgroundOpacity", 0);
                widget.writeConfig("pinnedLaunchers", ["applications:org.kde.dolphin.desktop", "applications:onyx-store.desktop", "applications:onyx-settings.desktop"]);
            }
        }
        dock.currentConfigGroup = ["ONYX"];
        dock.writeConfig("layoutVersion", "0.4.0-obryx");
    } catch (error) {
        if (dock) dock.remove();
        throw error;
    }
    // Preserve panels on other monitors. Only replace this screen's layout.
    for (var k = 0; k < previous.length; ++k) {
        if (previous[k].screen === dock.screen) previous[k].remove();
    }
    // Plasma owns Meta and Alt+F1 and activates our launchermenu provider.
    print("ONYX_LAYOUT_OK");
}());
