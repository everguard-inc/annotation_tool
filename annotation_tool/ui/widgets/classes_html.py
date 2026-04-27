from annotation_tool.core.models import LabelData
from annotation_tool.core.label_attributes import label_attributes_dict


def labels_to_html(title: str, labels: list[LabelData]) -> str:
    rows = []

    for label in labels:
        rows.append(
            "<tr>"
            f"<td>{label.hotkey}</td>"
            f"<td>{label.name}</td>"
            f"<td>{label.type.name}</td>"
            f"<td>{label.color}</td>"
            "</tr>"
        )

    added_keypoint_names = set()
    for label in labels:
        keypoint_info = label_attributes_dict(label.attributes).get("keypoint_info")
        if not isinstance(keypoint_info, dict):
            continue

        for keypoint_name, keypoint_data in keypoint_info.items():
            if keypoint_name in added_keypoint_names:
                continue
            color = (
                keypoint_data.get("color", "")
                if isinstance(keypoint_data, dict)
                else ""
            )
            rows.append(
                "<tr>"
                "<td></td>"
                f"<td>{keypoint_name}</td>"
                "<td>KEYPOINT</td>"
                f"<td>{color}</td>"
                "</tr>"
            )
            added_keypoint_names.add(keypoint_name)

    body = "\n".join(rows) if rows else "<tr><td colspan='4'>No labels</td></tr>"

    return f"""
    <html>
    <body>
        <h2>{title}</h2>
        <table border="1" cellspacing="0" cellpadding="6">
            <thead>
                <tr>
                    <th>Hotkey</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Color</th>
                </tr>
            </thead>
            <tbody>
                {body}
            </tbody>
        </table>
    </body>
    </html>
    """
