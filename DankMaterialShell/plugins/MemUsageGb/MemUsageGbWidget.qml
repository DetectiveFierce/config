import QtQuick
import qs.Common
import qs.Services
import qs.Widgets
import qs.Modules.Plugins

PluginComponent {
    id: root

    property var popoutService: null
    property var widgetData: null
    property bool minimumWidth: (widgetData && widgetData.minimumWidth !== undefined) ? widgetData.minimumWidth : true

    readonly property real usedMemoryGB: DgopService.usedMemoryKB > 0 ? (DgopService.usedMemoryKB / (1024 * 1024)) : 0
    readonly property string ramText: DgopService.usedMemoryKB > 0 ? (usedMemoryGB.toFixed(1) + " GB") : "--"

    Component.onCompleted: {
        DgopService.addRef(["memory"]);
    }

    Component.onDestruction: {
        DgopService.removeRef(["memory"]);
    }

    pillClickAction: (x, y, width, section, screen) => {
        DgopService.setSortBy("memory");
        popoutService?.toggleProcessList(x, y, width, section, screen);
    }

    horizontalBarPill: Component {
        Row {
            id: ramContent
            spacing: Theme.spacingXS

            DankIcon {
                name: "developer_board"
                size: Theme.barIconSize(root.barThickness, undefined, root.barConfig?.maximizeWidgetIcons, root.barConfig?.iconScale)
                color: {
                    if (DgopService.memoryUsage > 90) {
                        return Theme.tempDanger;
                    }

                    if (DgopService.memoryUsage > 75) {
                        return Theme.tempWarning;
                    }

                    return Theme.widgetIconColor;
                }
                anchors.verticalCenter: parent.verticalCenter
            }

            Item {
                anchors.verticalCenter: parent.verticalCenter
                implicitWidth: root.minimumWidth ? Math.max(ramBaseline.width, ramValue.paintedWidth) : ramValue.paintedWidth
                implicitHeight: ramValue.implicitHeight
                width: implicitWidth
                height: implicitHeight

                StyledTextMetrics {
                    id: ramBaseline
                    font.pixelSize: Theme.barTextSize(root.barThickness, root.barConfig?.fontScale, root.barConfig?.maximizeWidgetText)
                    text: "88.8 GB"
                }

                StyledText {
                    id: ramValue
                    anchors.fill: parent
                    text: root.ramText
                    font.pixelSize: Theme.barTextSize(root.barThickness, root.barConfig?.fontScale, root.barConfig?.maximizeWidgetText)
                    color: Theme.widgetTextColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideNone
                    wrapMode: Text.NoWrap
                }
            }
        }
    }

    verticalBarPill: Component {
        Column {
            spacing: 1

            DankIcon {
                name: "developer_board"
                size: Theme.barIconSize(root.barThickness, undefined, root.barConfig?.maximizeWidgetIcons, root.barConfig?.iconScale)
                color: {
                    if (DgopService.memoryUsage > 90) {
                        return Theme.tempDanger;
                    }

                    if (DgopService.memoryUsage > 75) {
                        return Theme.tempWarning;
                    }

                    return Theme.widgetIconColor;
                }
                anchors.horizontalCenter: parent.horizontalCenter
            }

            StyledText {
                text: DgopService.usedMemoryKB > 0 ? usedMemoryGB.toFixed(1) : "--"
                font.pixelSize: Theme.barTextSize(root.barThickness, root.barConfig?.fontScale, root.barConfig?.maximizeWidgetText)
                color: Theme.widgetTextColor
                anchors.horizontalCenter: parent.horizontalCenter
            }

            StyledText {
                text: "GB"
                font.pixelSize: Math.max(10, Theme.barTextSize(root.barThickness, root.barConfig?.fontScale, root.barConfig?.maximizeWidgetText) - 2)
                color: Theme.surfaceVariantText
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }
}
