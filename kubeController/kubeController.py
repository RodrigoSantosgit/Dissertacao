'''
	Rodrigo Santos, n mec 89180
	
	- Dissertation Project
	Computation Controller - Kubernetes Controller
'''

from kubernetes import config, dynamic
from kubernetes.client import api_client
from kafka import KafkaConsumer
from kafka import KafkaProducer

import kubernetes.client
import datetime
import pytz
import subprocess
import requests
import sys

# namespace test: "default"
# name test: "nginx-deployment"
# image test: "nginx:1.14.2"
# container name test: "nginx"
# app test: "nginx"

# name service test: "frontend-service"
# protocol test: "TCP"

#app = FastAPI()

global client
global networking_v1_api
global consumer
global producer
global expMngFncAPI

'''configuration = kubernetes.client.Configuration()
configuration.api_key['authorization'] = '754quh.kakrr1jsc4isb4oz'
configuration.api_key_prefix['authorization'] = 'Bearer'
configuration.host = "http://10.0.2.15"
configuration.verify_ssl = False

client = dynamic.DynamicClient(
        api_client.ApiClient(configuration)
)'''

consumer = KafkaConsumer("ComputationManagment", bootstrap_servers='10.0.2.15:9092')

producer = KafkaProducer(bootstrap_servers='10.0.2.15:9092')

client = dynamic.DynamicClient(
        api_client.ApiClient(configuration=config.load_kube_config(config_file='config/config'))
)

networking_v1_api = kubernetes.client.NetworkingV1Api()


###############################################
#		Main Cycle			#
###############################################
def main():

    global consumer
    
    while(True):
        for msg in consumer:
            processed_msg = msg.value.decode()
            log(processed_msg)
            checkAction(processed_msg)
            processed_msg = ''


###############################################
#		Check Action			#
###############################################
def checkAction(msg):

    global producer
    global expMngFncAPI
    
    processor, action, mode = msg.split(' ')[0:3]
    
    if processor != '[COMPUTATIONCONTROLLER]':
        return None

    ## INSTANTIATIONS ------
    if action == '[INSTANTIATE]':
        
        ## RIGHTAWAY MODE ------
        if mode == '[RIGHTAWAY]':
            log(" - creating deployment -")
            namespace, name, app, container_name, image = msg.split(' ')[3:]
            res_dep = create_deployment(namespace, name, app, container_name, image)
        
            # Create service
            log(" - creating service -")
            res_ser = create_service(name= name+"-service", selector=app, protocol="TCP", port = 5000, targetPort = 50000)
        
            if res_dep == {"SUCCESS"} and res_ser == {"SUCCESS"}:
                msg_out = '[NETCONTROLLER] [INSERT] IPV4SubEntry 10.30.0.30 3 10.0.2.15 08:00:27:93:75:80'
                producer.send('NetManagment', msg_out.encode())
            else:
                msg_out = '[MANAGMENT] [ERROR] [DELETE]'
                producer.send('ComputationManagment', msg_out.encode())
                
                
        ## TRIGGERBASED MODE ------
        if mode == '[TRIGGERED]':
            log(" - fetching deployment information -")
            
            port = msg.split(' ')[3:]
            info = requests.get("http://"+expMngFncAPI+":8000/fetchInfo?port=1").content.decode()
            
            namespace, name, app, container_name, image = info.replace('"', '').replace('[', '').replace(']','').split(",")

            log(" - creating deployment -")
            res_dep = create_deployment(namespace, name, app, container_name, image)
        
            # Create service
            log(" - creating service -")
            res_ser = create_service(name= name+"-service", selector=app, protocol="TCP", port = 5000, targetPort = 50000)
        
            if res_dep == {"SUCCESS"} and res_ser == {"SUCCESS"}:
                msg_out = '[NETCONTROLLER] [INSERT] IPV4SubEntry 10.30.0.30 3 10.0.2.15 08:00:27:93:75:80'
                producer.send('NetManagment', msg_out.encode())
            else:
                msg_out = '[MANAGMENT] [ERROR] [DELETE]'
                producer.send('ComputationManagment', msg_out.encode())
                

    ## DELETIONS ------
    if action == '[DELETE]':
    
        ## RIGHTAWAY MODE ------
        if mode == '[RIGHTAWAY]':
            log(" - deleting deployment -")
            namespace, name = msg.split(' ')[3:]
            res_dep = delete_deployment(namespace, name)
        
            # Delete service
            log(" - deleting service -")
            res_ser = delete_service(name="server-udp-service")
        
            if res_dep == {"SUCCESS"} and res_ser == {"SUCCESS"}:
                msg_out = '[NETCONTROLLER] [DELETE] IPV4SubEntry 10.30.0.30 3 10.0.2.15 08:00:27:93:75:80'
                producer.send('NetManagment', msg_out.encode())
            else:
                msg_out = '[MANAGMENT] [ERROR] [DELETE]'
                producer.send('ComputationManagment', msg_out.encode())
                
        ## TRIGGERBASED MODE ------
        if mode == '[TRIGGERED]':
            log(" - fetching deployment information -")
            
            port = msg.split(' ')[3:]
            info = requests.get("http://"+expMngFncAPI+":8000/fetchInfo?port=1").content.decode()
            
            if info != None and info != "null":
                namespace, name, app, container_name, image = info.replace('"', '').replace('[', '').replace(']','').split(",")
            
                log(" - deleting deployment -")
                res_dep = delete_deployment(namespace, name)
            
                # Delete service
                log(" - deleting service -")
                res_ser = delete_service(name="server-udp-service")
            
                if res_dep == {"SUCCESS"} and res_ser == {"SUCCESS"}:
                    msg_out = '[NETCONTROLLER] [DELETE] IPV4SubEntry 10.30.0.30 3 10.0.2.15 08:00:27:93:75:80'
                    producer.send('NetManagment', msg_out.encode())
                else:
                    msg_out = '[MANAGMENT] [ERROR] [DELETE]'
                    producer.send('ComputationManagment', msg_out.encode())
            else:
                msg_out = '[MANAGMENT] [ERROR] [DELETE] Nothing to delete!'
                producer.send('ComputationManagment', msg_out.encode())


###############################################
#			LOG			#
###############################################
def log(msg):

	# Building the command.
	command = ['echo', msg]

	subprocess.call(command)


###############################################
#		Create Deployemnt		#
###############################################
def create_deployment(namespace="default", name="None", app="None", container_name="None", image="None"):

    global client

    if name=="None" or app=="None" or container_name=="None" or image=="None":
        return {"ERROR"}

    # fetching the deployment api
    api = client.resources.get(api_version="apps/v1", kind="Deployment")

    deployment = ''

    try:
            
        deployment_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"labels": {"app": app}, "name": name},
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": app}},
                "template": {
                    "metadata": {"labels": {"app": app}},
                    "spec": {
                        "containers": [
                            {
                                "name": container_name,
                                "image": image,
                                "ports": [{"containerPort": 80}],
                                "imagePullPolicy": "Never",
                            }
                        ],
                        "restartPolicy": "Always",
                    },
                },
            },
        }

        # Creating deployment `nginx-deployment` in the `default` namespace
        deployment = api.create(body=deployment_manifest, namespace=namespace)
    except:
        deployment = ''
        print('\n[ERROR] Something went wrong!\n')
        return {"ERROR"}    
        

    # Listing deployment `nginx-deployment` in the `default` namespace
    '''deployment_created = api.get(name=name, namespace=namespace)

    print("%s\t%s\t\t\t%s\t%s" % ("NAMESPACE", "NAME", "REVISION", "RESTARTED-AT"))
    print(
        "%s\t\t%s\t%s\t\t%s\n"
        % (
            deployment_created.metadata.namespace,
            deployment_created.metadata.name,
            deployment_created.metadata.annotations,
            deployment_created.spec.template.metadata.annotations,
        )
    )'''

    print("\n[INFO] deployment `"+ name +"` created\n")
    return {"SUCCESS"}


###############################################
#		Delete Deployemnt		#
###############################################
def delete_deployment(namespace="default", name="None"):
    
    global client
    
    if name == "None":
       return {"ERROR"} 
    # fetching the deployment api
    api = client.resources.get(api_version="apps/v1", kind="Deployment")
    
    # Deleting deployment `nginx-deployment` from the `default` namespace
    try:
       deployment_deleted = api.delete(name=name, body={}, namespace=namespace)
       print("\n[INFO] deployment `"+ name +"` deleted\n")
       return {"SUCCESS"}
    except:
       print("\n[ERROR] Something went wrong!")
       return {"ERROR"}


###############################################
#		Create Service 		#
###############################################
def create_service(namespace="default", name="None", selector="None", protocol="None", port: int = 0, targetPort: int = 0):

    global client

    if name=="None" or protocol=="None" or port==0 or targetPort==0:
        {"ERROR"}

    # fetching the service api
    api = client.resources.get(api_version="v1", kind="Service")

    try:
        #namespace = input("\n\t -> Namespace: ")
        #name = input("\t -> Name: ")
        #protocol = input("\t -> Protocol: ")

        service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"labels": {"name": name}, "name": name, "resourceversion": "v1"},
            "spec": {
                "ports": [
                    {"name": "port", "port": port, "protocol": protocol, "targetPort": targetPort}
                ],
                "selector": {"name": selector},
            },
        }

        # Creating service `frontend-service` in the `default` namespace

        service = api.create(body=service_manifest, namespace=namespace)

        print("\n[INFO] service `"+ name + "` created\n")

        # Listing service `frontend-service` in the `default` namespace
        service_created = api.get(name=name, namespace=namespace)

        print("%s\t%s" % ("NAMESPACE", "NAME"))
        print(
            "%s\t\t%s\n"
            % (service_created.metadata.namespace, service_created.metadata.name)
        )

        # Patching the `spec` section of the `frontend-service`

        #service_manifest["spec"]["ports"] = [
        #    {"name": "new", "port": 8080, "protocol": protocol, "targetPort": 8080}
        #]

        #service_patched = api.patch(body=service_manifest, name=name, namespace=namespace)

    except:
        print("[ERROR] something went wrong!")
        return {"ERROR"}
    
    return {"SUCCESS"}


###############################################
#		Delete Service 		#
###############################################
def delete_service(namespace="default", name="None"):

    global client

    if name == "None":
       return {"ERROR"}

    # fetching the service api
    api = client.resources.get(api_version="v1", kind="Service")

    try:
       #namespace = input("\n\t -> Namespace: ")
       #name = input("\t -> Name: ")

       # Deleting service `frontend-service` from the `default` namespace
       service_deleted = api.delete(name=name, body={}, namespace=namespace)
       print("\n[INFO] service `" + name + "` deleted\n")
    except:
       print("\n[ERROR] something went wrong!")
       return {"ERROR"}
       
    return {"SUCCESS"}


###############################################
#		Create Ingress 		#
###############################################
def create_ingress(networking_v1_api):
    body = kubernetes.client.V1Ingress(
        api_version="networking.k8s.io/v1",
        kind="Ingress",
        metadata=kubernetes.client.V1ObjectMeta(name="ingress-example", annotations={
            "nginx.ingress.kubernetes.io/rewrite-target": "/"
        }),
        spec=kubernetes.client.V1IngressSpec(
            rules=[kubernetes.client.V1IngressRule(
                host="example.com",
                http=kubernetes.client.V1HTTPIngressRuleValue(
                    paths=[kubernetes.client.V1HTTPIngressPath(
                        path="/",
                        path_type="Exact",
                        backend=kubernetes.client.V1IngressBackend(
                            service=kubernetes.client.V1IngressServiceBackend(
                                port=kubernetes.client.V1ServiceBackendPort(
                                    number=5678,
                                ),
                                name="service-example")
                            )
                    )]
                )
            )
            ]
        )
    )
    # Creation of the Deployment in specified namespace
    # (Can replace "default" with a namespace you may have created)
    networking_v1_api.create_namespaced_ingress(
        namespace="default",
        body=body
    )


###############################################
#		Delete Ingress 		#
###############################################
def delete_ingress(networking_v1_api):
    
    # Creation of the Deployment in specified namespace
    networking_v1_api.delete_namespaced_ingress(
        name="ingress-example",
        namespace="default"
    )


###############################################
#		List Pods			#
###############################################
def list_pods():
    
    config.load_kube_config()

    v1 = kubernetes.client.CoreV1Api()
    print("\nListing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    print("IP\t\tNAMESPACE\t\tNAME")
    for i in ret.items:
        print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))


###############################################
#		List Services			#
###############################################
def list_services():
    
    config.load_kube_config()

    v1 = kubernetes.client.CoreV1Api()
    print("\nListing services with their IPs:")
    ret = v1.list_service_for_all_namespaces(watch=False)
    print("IP\t\tNAMESPACE\t\tNAME")
    for i in ret.items:
        print("%s\t%s\t%s" % (i.spec.cluster_ip, i.metadata.namespace, i.metadata.name))


###############################################
#		List Ingresses			#
###############################################
def list_ingresses(networking_v1_api):
    
    config.load_kube_config()

    print("\nListing ingresses with their HOSTs:")
    try:
        ret = networking_v1_api.list_ingress_for_all_namespaces(watch=False)
        print("HOST\t\tNAMESPACE\t\tNAME")
        for i in ret.items:
            print("%s\t%s\t%s" % (i.spec.rules.host, i.metadata.namespace, i.metadata.name))
    except:
        print("\n[INFO] no ingresses to show!")


################################################
if __name__ == "__main__":
    for i in range(1, len(sys.argv),2):
        if (sys.argv[i] == "--expMngFncAPI" or sys.argv[i] == "-api") and i != len(sys.argv) - 1:
            expMngFncAPI = sys.argv[i + 1]
    main()
