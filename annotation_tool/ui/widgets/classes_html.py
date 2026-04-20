from annotation_tool.core.models import LabelData


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
