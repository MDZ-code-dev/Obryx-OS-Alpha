// ONYX OS 0.3 native Plasma layout: functional launcher, apps and tray.
// Applied only once to the live user; existing panels are replaced.
var oldPanels = panels();
for (var i = oldPanels.length - 1; i >= 0; --i) {
    oldPanels[i].remove();
}
var dock = new Panel();
dock.location = "bottom";
dock.height = 54;
dock.floating = true;
dock.hiding = "none";
dock.alignment = "center";
dock.lengthMode = "fit";
dock.addWidget("org.kde.plasma.kickoff");
dock.addWidget("org.kde.plasma.icontasks");
dock.addWidget("org.kde.plasma.systemtray");
dock.addWidget("org.kde.plasma.digitalclock");
