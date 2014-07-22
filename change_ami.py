#!/usr/bin/env python
"""
Usage:

  $ ./change_ami.py <autoscale_group_name> <new_ami>

For example:

  $ ./change_ami.py www-django-d0staging-v060 ami-c7858dae

Now any future autoscaling events on that autoscale group will spin up
that AMI instead of the old one.

Combine this with an inplace deployment to have fast deployments and
autoscaling.

Example output would be something like:

    Found ASG
    Found Launch Config for ASG
    Creating new LC:  www-django-d0staging-v060-20140722152547-ami-c7858dae
    Updating autoscale group...
    Success!

"""

import sys
import time

from boto.ec2.autoscale import (
    AutoScaleConnection,
)


def get_asg_connection():
    conn = AutoScaleConnection()
    autoscale_groups = conn.get_all_groups(max_records=1)
    return conn


def update_ami(name, image_id):
    conn = get_asg_connection()
    autoscale_groups = conn.get_all_groups(names=[name], max_records=100)
    asg = autoscale_groups[0] if autoscale_groups else None

    if asg and asg.name == name:
        print "Found ASG"
        launch_configs = conn.get_all_launch_configurations(names=[asg.launch_config_name], max_records=100)
        lc = launch_configs[0] if launch_configs else None

        if lc and lc.name == asg.launch_config_name:
            # remove last trailing "-ami-<id>" from the launch config name
            # so we don't end up with "-ami-<id1>-ami-<id2>..."
            print "Found Launch Config for ASG (ami: {})".format(lc.image_id)
            name = lc.name.split("-ami-")[0]
            lc.name = name + "-" + image_id
            lc.image_id = image_id
            print "Creating new LC: ", lc.name
            new_lc = conn.create_launch_configuration(lc)
            print "Updating autoscale group..."
            asg.launch_config_name = lc.name
            asg.update()
            print "Success!"
    else:
        raise "Unable to find group!"

    return asg, lc


def main():
    if len(sys.argv) > 2:
        name = sys.argv[1]
        image_id = sys.argv[2]
        asg, lc = update_ami(name, image_id)
    else:
        print __doc__
        sys.exit(1)


if __name__=="__main__":
    main()
