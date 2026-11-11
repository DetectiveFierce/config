import QtQuick
import QtQuick.Controls
import Quickshell
import qs.Common
import qs.Widgets
import qs.Modules.Plugins

PluginComponent {
    id: root
    property var popoutService: null
    property var suggestions: []
    property var historyRows: []
    property var selected: null
    property var previewData: null
    property string cadence: "weekly"
    property string message: ""
    property bool busy: false
    property bool showHistory: false
    property bool showAllAffected: false
    property bool executionEnabled: false

    function planText(plan) {
        if (!plan) return "";
        let text = "Command: " + (plan.command || []).join(" ") + "\n";
        if (plan.bytes !== undefined) text += "Estimated immediate recovery: " + (plan.bytes / 1073741824).toFixed(2) + " GiB\n";
        if (plan.bytes_to_trash !== undefined) text += "Moved to Trash: " + (plan.bytes_to_trash / 1073741824).toFixed(2) + " GiB (not freed yet)\n";
        if (plan.restore) text += "Restore: " + plan.restore + "\n";
        if (plan.targets) text += "Affected packages: " + plan.targets.join(", ") + "\n";
        if (plan.files) {
            text += "Affected archives (" + plan.files.length + "):\n";
            let shown = root.showAllAffected ? plan.files : plan.files.slice(0, 30);
            text += shown.map(item => item[0]).join("\n");
            if (!root.showAllAffected && plan.files.length > 30) text += "\n… " + (plan.files.length - 30) + " more";
        }
        if (plan.path) text += "Path: " + plan.path + "\n";
        if (plan.install_dir) text += "Game install: " + plan.install_dir + "\n";
        if (plan.keep) text += "Keep: " + plan.keep + "\n";
        if (plan.image_id) text += "Image: " + plan.image_id + "\n";
        return text;
    }

    function call(args, done) {
        let timeout = args[0] === "analyze" ? 600000 : (args[0] === "execute" ? 360000 : (args[0] === "preview" ? 120000 : 30000));
        Proc.runCommand(null,
                        ["/home/shared-psychosis/.local/bin/storage-advisor"].concat(args),
                        (stdout, code) => {
            let value = {};
            try { value = JSON.parse(stdout); }
            catch (e) { value = {"error": "Invalid response from local advisor"}; }
            if (code !== 0 && !value.error)
                value.error = "Advisor exited with status " + code;
            if (value.error) root.message = value.error;
            done(value);
        }, 0, timeout, root);
    }

    function refresh() {
        call(["list"], value => {
            if (!value.error) {
                suggestions = value.suggestions || [];
                cadence = value.cadence || "weekly";
                executionEnabled = !!value.execution_enabled;
            }
        });
    }

    function analyze() {
        busy = true;
        message = "Analyzing locally…";
        call(["analyze"], value => {
            busy = false;
            message = value.error || "Analysis complete";
            refresh();
        });
    }

    function choose(item) {
        selected = selected && selected.id === item.id ? null : item;
        previewData = null;
        showAllAffected = false;
    }

    function preview() {
        if (!selected) return;
        call(["preview", selected.id], value => {
            previewData = value.error ? null : value;
        });
    }

    function execute() {
        if (!selected || !previewData) return;
        let id = selected.id;
        let token = previewData.token;
        busy = true;
        call(["execute", id, "--token", token], value => {
            busy = false;
            previewData = null;
            selected = null;
            message = value.error || (value.pending_external ? "Steam uninstall opened; confirm in Steam." : (value.ok ? "Action completed" : "Action failed"));
            refresh();
        });
    }

    function reject() {
        if (!selected) return;
        call(["reject", selected.id], value => {
            if (!value.error) {
                selected = null;
                previewData = null;
                refresh();
            }
        });
    }

    Component.onCompleted: refresh()
    Timer { interval: 300000; repeat: true; running: true; onTriggered: root.refresh() }
    popoutWidth: 560
    popoutHeight: 650

    horizontalBarPill: Component {
        Row {
            spacing: Theme.spacingXS
            DankIcon {
                name: "inventory_2"
                size: Theme.barIconSize(root.barThickness, undefined, root.barConfig?.maximizeWidgetIcons, root.barConfig?.iconScale)
                color: Theme.widgetIconColor
                anchors.verticalCenter: parent.verticalCenter
            }
            StyledText {
                text: root.suggestions.length > 0 ? String(root.suggestions.length) : "✓"
                color: Theme.widgetTextColor
                font.pixelSize: Theme.barTextSize(root.barThickness, root.barConfig?.fontScale, root.barConfig?.maximizeWidgetText)
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    verticalBarPill: Component {
        Column {
            spacing: 2
            DankIcon { name: "inventory_2"; size: Theme.iconSizeSmall; color: Theme.widgetIconColor }
            StyledText { text: String(root.suggestions.length); color: Theme.widgetTextColor }
        }
    }

    popoutContent: Component {
        PopoutComponent {
            headerText: "Storage Advisor"
            detailsText: "Local review · no API calls"
            showCloseButton: true

            Column {
                width: parent.width
                spacing: 8
                Row {
                    spacing: 8
                    Button { text: root.busy ? "Analyzing…" : "Analyze now"; enabled: !root.busy; onClicked: root.analyze() }
                    Button {
                        text: root.cadence === "weekly" ? "Weekly ▾" : "Daily ▾"
                        onClicked: root.call(["settings", "--cadence", root.cadence === "weekly" ? "daily" : "weekly"], value => {
                            if (!value.error) root.cadence = value.cadence;
                        })
                    }
                    Button {
                        text: root.showHistory ? "Suggestions" : "History"
                        onClicked: {
                            root.showHistory = !root.showHistory;
                            if (root.showHistory) root.call(["history"], value => root.historyRows = value.history || []);
                        }
                    }
                }
                StyledText {
                    width: parent.width
                    text: root.message || (root.suggestions.length ? "Expand a row to review the evidence." : "No new suggestions. Run Analyze now for a current report.")
                    color: Theme.surfaceText
                    wrapMode: Text.Wrap
                }
                ScrollView {
                    width: parent.width
                    height: 500
                    contentWidth: availableWidth
                    Column {
                        width: parent.width
                        spacing: 8
                        Repeater {
                            model: root.showHistory ? root.historyRows : root.suggestions
                            delegate: Rectangle {
                                required property var modelData
                                width: parent.width
                                height: body.implicitHeight + 16
                                radius: 8
                                color: Theme.surfaceContainerHigh
                                Column {
                                    id: body
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.top: parent.top
                                    anchors.margins: 8
                                    spacing: 5
                                    StyledText {
                                        width: parent.width
                                        text: root.showHistory ? modelData.decision + " · " + (modelData.title || modelData.suggestion_id) : modelData.title + "  ▾"
                                        font.bold: true
                                        color: Theme.surfaceText
                                        wrapMode: Text.Wrap
                                        MouseArea { anchors.fill: parent; enabled: !root.showHistory; onClicked: root.choose(modelData) }
                                    }
                                    StyledText {
                                        visible: !root.showHistory
                                        width: parent.width
                                        text: modelData.group_name + " · " + modelData.confidence + " confidence · " +
                                              (modelData.estimated_bytes > 0 ? (modelData.estimated_bytes / 1073741824).toFixed(2) + " GiB possible" : "no immediate free space")
                                        color: Theme.surfaceText
                                        wrapMode: Text.Wrap
                                    }
                                    Column {
                                        visible: !root.showHistory && root.selected && root.selected.id === modelData.id
                                        width: parent.width
                                        spacing: 5
                                        StyledText { width: parent.width; text: modelData.claim; color: Theme.surfaceText; wrapMode: Text.Wrap }
                                        StyledText { width: parent.width; text: "Evidence: " + JSON.stringify(modelData.evidence || {}, null, 2); color: Theme.surfaceText; wrapMode: Text.Wrap }
                                        Row {
                                            visible: !!(modelData.evidence && modelData.evidence.comparison_required)
                                            width: parent.width
                                            spacing: 8
                                            Column {
                                                width: (parent.width - 8) / 2
                                                StyledText { width: parent.width; text: "Proposed for Trash\n" + (modelData.evidence ? modelData.evidence.remove : ""); color: Theme.surfaceText; wrapMode: Text.Wrap }
                                                Button { text: "Open proposed copy"; onClicked: { if (modelData.evidence) Quickshell.execDetached(["xdg-open", modelData.evidence.remove]); } }
                                            }
                                            Column {
                                                width: (parent.width - 8) / 2
                                                StyledText { width: parent.width; text: "Keep\n" + (modelData.evidence ? modelData.evidence.keep : ""); color: Theme.surfaceText; wrapMode: Text.Wrap }
                                                Button { text: "Open kept copy"; onClicked: { if (modelData.evidence) Quickshell.execDetached(["xdg-open", modelData.evidence.keep]); } }
                                            }
                                        }
                                        StyledText { width: parent.width; text: "Risk: " + modelData.risk + ". Review affected items before accepting."; color: Theme.surfaceText; wrapMode: Text.Wrap }
                                        Row {
                                            spacing: 8
                                            Button { text: "Fresh preview"; onClicked: root.preview() }
                                            Button { text: "Reject"; onClicked: root.reject() }
                                        }
                                        Column {
                                            visible: root.previewData && root.previewData.suggestion.id === modelData.id
                                            width: parent.width
                                            spacing: 5
                                            StyledText { width: parent.width; text: root.planText(root.previewData ? root.previewData.plan : null); color: Theme.surfaceText; wrapMode: Text.Wrap }
                                            Button {
                                                visible: root.previewData && root.previewData.plan.files && root.previewData.plan.files.length > 30
                                                text: root.showAllAffected ? "Show fewer" : "Show all affected archives"
                                                onClicked: root.showAllAffected = !root.showAllAffected
                                            }
                                            StyledText {
                                                width: parent.width
                                                text: root.previewData && (root.previewData.plan.type === "trash_file" || root.previewData.plan.type === "trash_directory")
                                                      ? "Final confirmation: move the shown target to Trash. Space is freed when Trash is emptied."
                                                      : root.previewData && root.previewData.plan.type === "steam_uninstall"
                                                        ? "Final confirmation: open Steam's uninstall dialog for this game. Confirm there to finish."
                                                        : "Final confirmation: run the shown removal command now."
                                                color: Theme.surfaceText
                                                wrapMode: Text.Wrap
                                            }
                                            StyledText { visible: !root.executionEnabled; width: parent.width; text: "Execution awaits review of the first live report."; color: Theme.surfaceText; wrapMode: Text.Wrap }
                                            Button { text: "Confirm and execute"; enabled: !root.busy && root.executionEnabled; onClicked: root.execute() }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
