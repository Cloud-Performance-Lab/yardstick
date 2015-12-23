# yardstick comment: this file is a modified copy of
# influxdb-python/influxdb/line_protocol.py

from __future__ import unicode_literals
from copy import copy

from six import binary_type, text_type, integer_types


def _escape_tag(tag):
    tag = _get_unicode(tag, force=True)
    return tag.replace(
        "\\", "\\\\"
    ).replace(
        " ", "\\ "
    ).replace(
        ",", "\\,"
    ).replace(
        "=", "\\="
    )


def _escape_value(value):
    value = _get_unicode(value)
    if isinstance(value, text_type) and value != '':
        return "\"{}\"".format(
            value.replace(
                "\"", "\\\""
            ).replace(
                "\n", "\\n"
            )
        )
    elif isinstance(value, integer_types) and not isinstance(value, bool):
        return str(value) + 'i'
    else:
        return str(value)


def _get_unicode(data, force=False):
    """
    Try to return a text aka unicode object from the given data.
    """
    if isinstance(data, binary_type):
        return data.decode('utf-8')
    elif data is None:
        return ''
    elif force:
        return str(data)
    else:
        return data


def make_lines(data):
    """
    Extracts the points from the given dict and returns a Unicode string
    matching the line protocol introduced in InfluxDB 0.9.0.

    line protocol format:
        <measurement>[,<tag-key>=<tag-value>...] <field-key>=<field-value>\
            [,<field2-key>=<field2-value>...] [unix-nano-timestamp]

    Ref:
        https://influxdb.com/docs/v0.9/write_protocols/write_syntax.html
        https://influxdb.com/docs/v0.9/write_protocols/line.html
    """
    lines = []
    static_tags = data.get('tags', None)
    for point in data['points']:
        elements = []

        # add measurement name
        measurement = _escape_tag(_get_unicode(
            point.get('measurement', data.get('measurement'))
        ))
        key_values = [measurement]

        # add tags
        if static_tags is None:
            tags = point.get('tags', {})
        else:
            tags = copy(static_tags)
            tags.update(point.get('tags', {}))

        # tags should be sorted client-side to take load off server
        for tag_key in sorted(tags.keys()):
            key = _escape_tag(tag_key)
            value = _escape_tag(tags[tag_key])

            if key != '' and value != '':
                key_values.append("{key}={value}".format(key=key, value=value))
        key_values = ','.join(key_values)
        elements.append(key_values)

        # add fields
        field_values = []
        for field_key in sorted(point['fields'].keys()):
            key = _escape_tag(field_key)
            value = _escape_value(point['fields'][field_key])
            if key != '' and value != '':
                field_values.append("{key}={value}".format(
                    key=key,
                    value=value
                ))
        field_values = ','.join(field_values)
        elements.append(field_values)

        # add timestamp
        if 'time' in point:
            elements.append(point['time'])

        line = ' '.join(elements)
        lines.append(line)
    lines = '\n'.join(lines)
    return lines + '\n'
