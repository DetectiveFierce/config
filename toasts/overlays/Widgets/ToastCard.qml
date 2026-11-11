import QtQuick

// Reference layout: quiet mono header, readable title, full-width action footer.
Item {
    id: card
    property string appName: "System"
    property string summary: ""
    property string detail: ""
    property bool expanded: false
    property bool fileDrop: false
    property var actions: []
    property real progress: 1
    signal actionInvoked(string key)
    readonly property string sender: summary.replace(/ wants to send.*$/, "")
    readonly property string rest: fileDrop ? summary.slice(sender.length) : ""
    readonly property string firstDetail: detail.split("\n")[0]
    readonly property bool hasFooter: actions.length > 0
    implicitHeight: (firstDetail.length > 0 ? 71 + detailLine.height : 68) + (hasFooter ? 40 : 0)
    Rectangle { anchors.fill: parent; radius: 8; color: "#172304" }
    Column {
        x: 16; y: 12; width: parent.width-32; spacing: 0
        Row {
            spacing: 7; height: 12
            Rectangle { width: 5; height: 5; radius: 2.5; color: "#a6e22e"; anchors.verticalCenter: parent.verticalCenter }
            Text {
                text: card.appName.toUpperCase()
                color: "#8fa66a"; font.family: "IBM Plex Mono"; font.pixelSize: 10; font.letterSpacing: 1.2
            }
        }
        Item { width: 1; height: 8 }
        Text {
            width: parent.width; height: 20
            text: card.fileDrop ? "<span style='color:#f1fadc;font-weight:500'>" + card.sender.replace(/&/g,"&amp;").replace(/</g,"&lt;") + "</span>" + card.rest.replace(/&/g,"&amp;").replace(/</g,"&lt;") : card.summary
            textFormat: card.fileDrop ? Text.RichText : Text.PlainText
            font.family: "IBM Plex Sans"; font.pixelSize: 16; font.weight: Font.Normal
            color: card.fileDrop ? "#9db07a" : "#f1fadc"
            maximumLineCount: 1; elide: Text.ElideRight
        }
        Item { width: 1; height: 3; visible: card.firstDetail.length > 0 }
        Text {
            id: detailLine
            width: parent.width; height: card.expanded ? Math.min(160, implicitHeight) : 17; visible: card.firstDetail.length > 0
            text: card.expanded ? card.detail : (card.fileDrop ? card.firstDetail.replace(/( \+ \d+ more.*| · [^·]+$)/, "<span style='color:#7f9460'>$1</span>") : card.firstDetail); textFormat: Text.RichText
            font.family: "IBM Plex Mono"; font.pixelSize: 12; color: "#c9dba3"
            maximumLineCount: card.expanded ? -1 : 1; wrapMode: card.expanded ? Text.Wrap : Text.NoWrap; elide: Text.ElideRight
        }
    }
    // Clip the footer to the same rounded lower corners without rounding its top edge.
    Rectangle {
        anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
        anchors.leftMargin: 3; anchors.rightMargin: 3; anchors.bottomMargin: 3
        height: 40; visible: card.hasFooter; radius: 8; color: "#172304"; clip: true
        Rectangle { x: 0; y: 0; width: parent.width; height: 8; color: "#172304" }
        Row {
            anchors.fill: parent
            Repeater {
                model: card.actions
                Rectangle {
                    required property var modelData
                    required property int index
                    readonly property bool accept: modelData.key === "accept"
                    width: (card.width-6) / Math.max(1, card.actions.length); height: 40
                    radius: 8
                    color: accept ? (mouse.containsMouse ? "#b4ed45" : "#a6e22e") : (mouse.containsMouse ? "#263811" : "#172304")
                    Rectangle { x: 0; y: 0; width: parent.width; height: 8; color: parent.color }
                    Rectangle { anchors.left: parent.left; width: 8; height: parent.height; visible: index > 0; color: parent.color }
                    Rectangle { anchors.right: parent.right; width: 8; height: parent.height; visible: index < card.actions.length-1; color: parent.color }
                    Text {
                        x: 16; anchors.verticalCenter: parent.verticalCenter
                        text: modelData.label; font.family: "IBM Plex Sans"; font.pixelSize: 13; font.weight: Font.Medium
                        color: parent.accept ? "#172304" : "#c9dba3"
                    }
                    Text {
                        anchors.right: parent.right; anchors.rightMargin: 16; anchors.verticalCenter: parent.verticalCenter
                        text: modelData.shortcut ?? ""; font.family: "IBM Plex Mono"; font.pixelSize: 11
                        color: parent.accept ? "#405d14" : "#8fa66a"
                    }
                    Rectangle { width: 1; height: parent.height; visible: index > 0; color: "#4a6519" }
                    MouseArea { id: mouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: card.actionInvoked(modelData.key) }
                }
            }
        }
        Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: "#4a6519" }
    }
    CountdownBorder { anchors.fill: parent; z: 200; progress: card.progress }
}
