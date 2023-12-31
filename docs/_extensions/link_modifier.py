from docutils import nodes
from sphinx.transforms import SphinxTransform

REPLACEMENTS = {
    'https://github.com/JELLO-W/yaw/tree/master/yaw_extensions/yarp/README.md':
        'yarp_install_lnk.html',
    'https://github.com/JELLO-W/yaw/tree/master/yaw_extensions/yaw_ros2_interfaces/README.md':
        'ros2_interfaces_lnk.html',
    'https://github.com/JELLO-W/yaw/tree/master/yaw_extensions/yaw_ros_interfaces/README.md':
        'ros_interfaces_lnk.html'
    }


class LinkModifier(SphinxTransform):
    default_priority = 999

    def apply(self):
        for node in self.document.traverse(nodes.reference):
            uri = node.get('refuri', '')
            for links in REPLACEMENTS.keys():
                if links in uri:
                    node['refuri'] = uri.replace(links, REPLACEMENTS[links])


def setup(app):
    app.add_transform(LinkModifier)
