// Plasma 6 scripting API. A failed replacement preserves the existing panels.
(function () {
    var previous = panels();
    var dock = null;
    var launcher = null;
    for (var i = 0; i < previous.length; ++i) {
        previous[i].currentConfigGroup = ["ONYX"];
        if (previous[i].readConfig("layoutVersion", "") === "0.3.3") {
            print("ONYX_LAYOUT_OK");
            return;
        }
    }
    try {
        dock = new Panel();
        dock.location = "bottom";
        dock.height = 66;
        dock.floating = true;
        dock.alignment = "center";
        dock.lengthMode = "fit";
        dock.hiding = "none";
        dock.opacity = "translucent";
        var types = ["org.onyx.home", "per.nonobeam.paneldock",
                     "org.kde.plasma.systemtray", "org.kde.plasma.digitalclock"];
        for (var j = 0; j < types.length; ++j) {
            var widget = dock.addWidget(types[j]);
            if (!widget || widget.type !== types[j]) {
                throw new Error("Cannot create required widget: " + types[j]);
            }
            if (j === 0) launcher = widget;
            if (j === 1) {
                widget.currentConfigGroup = ["General"];
                widget.writeConfig("iconSize", 35);
                widget.writeConfig("hoverScale", 1.35);
                widget.writeConfig("hoverLift", 3);
                widget.writeConfig("backgroundOpacity", 0);
                widget.writeConfig("pinnedLaunchers", ["applications:org.kde.dolphin.desktop", "applications:onyx-store.desktop", "applications:onyx-settings.desktop"]);
            }
        }
        dock.currentConfigGroup = ["ONYX"];
        dock.writeConfig("layoutVersion", "0.3.3");
    } catch (error) {
        if (dock) dock.remove();
        throw error;
    }
    // Preserve panels on other monitors. Only replace this screen's layout.
    for (var k = 0; k < previous.length; ++k) {
        if (previous[k].screen === dock.screen) previous[k].remove();
    }
    launcher.globalShortcut = "Alt+F1";
    print("ONYX_LAYOUT_OK");
}());
