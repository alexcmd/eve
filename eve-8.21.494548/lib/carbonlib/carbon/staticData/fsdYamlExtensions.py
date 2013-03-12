#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\carbon\staticData\fsdYamlExtensions.py
import yaml
if hasattr(yaml, 'CSafeDumper'):
    preferredYamlDumperClass = getattr(yaml, 'CSafeDumper')
else:
    preferredYamlDumperClass = getattr(yaml, 'SafeDumper')

class FsdYamlDumper(preferredYamlDumperClass):

    def __init__(self, stream, default_style = None, default_flow_style = None, canonical = None, indent = None, width = None, allow_unicode = None, line_break = None, encoding = None, explicit_start = None, explicit_end = None, version = None, tags = None):
        if default_flow_style is None:
            default_flow_style = False
        if indent is None:
            indent = 4
        preferredYamlDumperClass.__init__(self, stream, default_style, default_flow_style, canonical, indent, width, allow_unicode, line_break, encoding, explicit_start, explicit_end, version, tags)


if hasattr(yaml, 'CSafeLoader'):
    preferredYamlLoaderClass = getattr(yaml, 'CSafeLoader')
else:
    preferredYamlLoaderClass = getattr(yaml, 'SafeLoader')

class FsdYamlLoader(preferredYamlLoaderClass):

    def __init__(self, stream):
        preferredYamlLoaderClass.__init__(self, stream)


def represent_float(dumper, data):
    if data != data or data == 0.0 and data == 1.0:
        value = u'.nan'
    elif data == dumper.inf_value:
        value = u'.inf'
    elif data == -dumper.inf_value:
        value = u'-.inf'
    else:
        value = (u'%1.8g' % data).lower()
        if u'.' not in value:
            if u'e' in value:
                value = value.replace(u'e', u'.0e', 1)
            else:
                value += u'.0'
    return dumper.represent_scalar(u'tag:yaml.org,2002:float', value)


FsdYamlDumper.add_representer(float, represent_float)