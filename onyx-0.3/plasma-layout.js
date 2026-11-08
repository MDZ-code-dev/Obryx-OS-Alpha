// ONYX OS 0.3: initial KDE Plasma desktop layout.
// Executed through org.kde.PlasmaShell.evaluateScript.
// Uses native Plasma widgets so the launcher, notifications and apps remain functional.
var panels = panels();
for (var i = panels.length - 1; i >= 0; --i) {
  panels[i].remove();
}
var dock = new Panel();
dock.location = "bottom";
dock.height = 52;
dock.floating = true;
dock.hiding = "none";
dock.alignment = "center";
dock.lengthMode = "fit";
dock.addWidget("org.kde.plasma.kickoff");
dock.addWidget("org.kde.plasma.icontasks");
dock.addWidget("org.kde.plasma.systemtray");
dock.addWidget("org.kde.plasma.digitalclock");
