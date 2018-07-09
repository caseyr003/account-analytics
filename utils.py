import json
import os
import time
import oci
from oci.object_storage.transfer.constants import MEBIBYTE
import html.parser as htmlparser

class OCI(object):
    def __init__(self, tenancy_ocid, user_ocid, region, fingerprint, key_location, key,
                 compartment_ocid, config_file):
        self.tenancy_ocid = tenancy_ocid
        self.user_ocid = user_ocid
        self.region = region
        self.fingerprint = fingerprint
        self.key_location = key_location
        self.compartment_ocid = compartment_ocid
        self.config_file = config_file
        self.key = key

    def config_account(self):
        config = open(self.config_file, 'w')
        config.seek(0)
        config.truncate()
        config.write('[DEFAULT]\n')
        config.write('user=%s\n' % self.user_ocid)
        config.write('fingerprint=%s\n' % self.fingerprint)
        config.write('key_file=%s\n' % self.key_location)
        config.write('tenancy=%s\n' % self.tenancy_ocid)
        config.write('region=%s\n' % self.region)
        config.write('compartment=%s\n' % self.compartment_ocid)
        config.close()

    def config_key(self):
        config = open("api_key.pem", 'w')
        config.seek(0)
        config.truncate()
        config.write(self.key)
        config.close()

    def is_active(self):
        self.config_key()
        self.config_account()

        success = False
        try:
            config = oci.config.from_file(file_location=self.config_file)
            identity = oci.identity.IdentityClient(config)
            user = identity.get_user(config["user"])
            success = True
        except:
            print("An Error Occured")

        return success

    def get_compartment(self):
        config = oci.config.from_file(file_location=self.config_file)
        identity = oci.identity.IdentityClient(config)
        compartment = identity.get_compartment(self.compartment_ocid).data
        return compartment


    def get_instance_list(self):
        config = oci.config.from_file(file_location=self.config_file)
        compute_store = oci.core.compute_client.ComputeClient(config)
        instance_list = compute_store.list_instances(self.compartment_ocid)
        data = {}
        for item in instance_list.data:
            vnic = self.get_vnic_attachments(item.id)
            subnet_ocid = vnic[0].subnet_id
            instance = {"name": item.display_name,
                        "type": "instance",
                        "size": int(item.shape.split(".")[2]),
                        "ocid": item.id,
                        "tags": item.freeform_tags,
                        "subnet_ocid": subnet_ocid,
                        "vnic_ocid": vnic[0].vnic_id,
                        "shape": item.shape,
                        "created": str(item.time_created),
                        "lifecycle_state": item.lifecycle_state,
                        "availability_domain": vnic[0].availability_domain}

            if subnet_ocid in data:
                data[subnet_ocid]["children"].append(instance)
            else:
                data[subnet_ocid] = { "children": [instance] }

        return data


    def get_json(self):
        return json.dumps(self.get_vcns(), indent=4)


    def get_vcns(self):
        compartment = self.get_compartment()
        data = { "name": compartment.name,
                 "type": "compartment",
                 "ocid": compartment.compartment_id,
                 "tags": compartment.freeform_tags,
                 "created": str(compartment.time_created),
                 "lifecycle_state": compartment.lifecycle_state,
                 "children": []}
        config = oci.config.from_file(file_location=self.config_file)
        network_client = oci.core.virtual_network_client.VirtualNetworkClient(config)
        vcn_list = network_client.list_vcns(compartment_id=self.compartment_ocid).data
        for x in vcn_list:
            subnets = self.get_subnets(x.id)
            data["children"].append({"name": x.display_name,
                                     "type": "vcn",
                                     "ocid": x.id,
                                     "tags": x.freeform_tags,
                                     "created": str(x.time_created),
                                     "lifecycle_state": x.lifecycle_state,
                                     "domain_name": x.vcn_domain_name,
                                     "children": subnets})
        return data

    def get_subnets(self, vcn_ocid):
        config = oci.config.from_file(file_location=self.config_file)
        network_client = oci.core.virtual_network_client.VirtualNetworkClient(config)
        data = []
        subnet_list = network_client.list_subnets(compartment_id=self.compartment_ocid,
                                                  vcn_id=vcn_ocid).data
        instance_list = self.get_instance_list()
        for x in subnet_list:
            if x.id in instance_list:
                data.append({"name": x.display_name,
                             "type": "subnet",
                             "ocid": x.id,
                             "tags": x.freeform_tags,
                             "lifecycle_state": x.lifecycle_state,
                             "created": str(x.time_created),
                             "children": instance_list[x.id]["children"]})
            else:
                data.append({"name": x.display_name,
                             "type": "subnet",
                             "ocid": x.id,
                             "tags": x.freeform_tags,
                             "lifecycle_state": x.lifecycle_state,
                             "created": str(x.time_created),
                             "children": []})
        return data

    def get_vnic_attachments(self, instance_ocid):
        config = oci.config.from_file(file_location=self.config_file)
        compute_store = oci.core.compute_client.ComputeClient(config)
        vnic_list = compute_store.list_vnic_attachments(self.compartment_ocid,
                                                        instance_id=instance_ocid).data
        data = []
        for x in vnic_list:
            data.append(x)
        return data
