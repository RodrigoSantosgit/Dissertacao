from kubernetes import config, dynamic
from kubernetes.client import api_client
import kubernetes.client
import datetime
import pytz
import p4runtime

# namespace test: "default"
# name test: "nginx-deployment"
# image test: "nginx:1.14.2"
# container name test: "nginx"
# app test: "nginx"

# name service test: "frontend-service"
# protocol test: "TCP"

global client

def main():
    # Creating a dynamic client
    global client
    
    client = dynamic.DynamicClient(
        api_client.ApiClient(configuration=config.load_kube_config())
    )
    networking_v1_api = kubernetes.client.NetworkingV1Api()
    
    op = '99'
    while op != '0':
    	print("\n -> KUBE CONTROLLER:\n" +
    		"\t1 - Create Deployment\n" +
    		"\t2 - Delete Deployment\n" +
    		"\t3 - Create Service\n" +
    		"\t4 - Delete Service\n" +
    		"\t5 - Create Ingress\n" +
    		"\t6 - Delete Ingress\n" +
    		"\t7 - List Pods\n" +
    		"\t8 - List Services\n" +
    		"\t9 - List Ingresses\n" +
    		"\t0 - Exit\n")
    	op = input("[OPTION] -> ")

    	if op == '1':
    	    create_deployment()
    	if op == '2':
    	    delete_deployment()
    	if op == '3':
    	    create_service()
    	if op == '4':
    	    delete_service()
    	if op == '5':
    	    create_ingress(networking_v1_api)
    	if op == '6':
    	    delete_ingress(networking_v1_api)
    	if op == '7':
    	    list_pods()
    	if op == '8':
    	    list_services()
    	if op == '9':
    	    list_ingresses(networking_v1_api)

    print('\n[EXITING]\n')


###############################################
#		Create Deployemnt		#
###############################################
def create_deployment():

    global client
    
    # fetching the deployment api
    api = client.resources.get(api_version="apps/v1", kind="Deployment")

    deployment = ''

    while deployment == '':
        try:
            namespace = input("\n\t -> Namespace: ")
            name = input("\t -> Name: ")
            app = input ("\t -> App: ")
            container_name = input("\t -> Container name: ")
            image = input("\t -> Image: ")
            
            
            deployment_manifest = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {"labels": {"app": app}, "name": name},
                "spec": {
                    "replicas": 3,
                    "selector": {"matchLabels": {"app": app}},
                    "template": {
                        "metadata": {"labels": {"app": app}},
                        "spec": {
                            "containers": [
                                {
                                    "name": container_name,
                                    "image": image,
                                    "ports": [{"containerPort": 80}],
                                }
                            ]
                        },
                    },
                },
            }

            # Creating deployment `nginx-deployment` in the `default` namespace
            deployment = api.create(body=deployment_manifest, namespace=namespace)
        except:
            deployment = ''
            print('\n[ERROR] Something went wrong!\n')
        finally:    
            print("\n[INFO] deployment `"+ name +"` created\n")

    # Listing deployment `nginx-deployment` in the `default` namespace
    deployment_created = api.get(name=name, namespace=namespace)

    print("%s\t%s\t\t\t%s\t%s" % ("NAMESPACE", "NAME", "REVISION", "RESTARTED-AT"))
    print(
        "%s\t\t%s\t%s\t\t%s\n"
        % (
            deployment_created.metadata.namespace,
            deployment_created.metadata.name,
            deployment_created.metadata.annotations,
            deployment_created.spec.template.metadata.annotations,
        )
    )

    # Patching the `spec.template.metadata` section to add `kubectl.kubernetes.io/restartedAt` annotation
    # In order to perform a rolling restart on the deployment `nginx-deployment`

    deployment_manifest["spec"]["template"]["metadata"] = {
        "annotations": {
            "kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow()
            .replace(tzinfo=pytz.UTC)
            .isoformat()
        }
    }

    deployment_patched = api.patch(
        body=deployment_manifest, name=name, namespace=namespace
    )

    print("\n[INFO] deployment `"+ name +"` restarted\n")
    print(
        "%s\t%s\t\t\t%s\t\t\t\t\t\t%s"
        % ("NAMESPACE", "NAME", "REVISION", "RESTARTED-AT")
    )
    print(
        "%s\t\t%s\t%s\t\t%s\n"
        % (
            deployment_patched.metadata.namespace,
            deployment_patched.metadata.name,
            deployment_patched.metadata.annotations,
            deployment_patched.spec.template.metadata.annotations,
        )
    )


###############################################
#		Delete Deployemnt		#
###############################################
def delete_deployment():
    
    global client
    
    # fetching the deployment api
    api = client.resources.get(api_version="apps/v1", kind="Deployment")
    
    # Deleting deployment `nginx-deployment` from the `default` namespace
    try:
       namespace = input("\n\t -> Namespace: ")
       name = input("\t -> Name: ")
       deployment_deleted = api.delete(name=name, body={}, namespace=namespace)
    except:
       print("\n[ERROR] Something went wrong!")
    finally:
       print("\n[INFO] deployment `"+ name +"` deleted")


###############################################
#		Create Service 		#
###############################################
def create_service():

    global client

    # fetching the service api
    api = client.resources.get(api_version="v1", kind="Service")

    try:
        namespace = input("\n\t -> Namespace: ")
        name = input("\t -> Name: ")
        protocol = input("\t -> Protocol: ")

        service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"labels": {"name": name}, "name": name, "resourceversion": "v1"},
            "spec": {
                "ports": [
                    {"name": "port", "port": 80, "protocol": protocol, "targetPort": 80}
                ],
                "selector": {"name": name},
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

        service_manifest["spec"]["ports"] = [
            {"name": "new", "port": 8080, "protocol": protocol, "targetPort": 8080}
        ]

        service_patched = api.patch(body=service_manifest, name=name, namespace=namespace)

    except:
        print("[ERROR] something went wrong!")
    finally:
        print("\n[INFO] service `"+ name + "` patched\n")
        print("%s\t%s\t\t\t%s" % ("NAMESPACE", "NAME", "PORTS"))
        print(
            "%s\t\t%s\t%s\n"
            % (
                service_patched.metadata.namespace,
                service_patched.metadata.name,
                service_patched.spec.ports,
            )
        )


###############################################
#		Delete Service 		#
###############################################
def delete_service():

    global client

    # fetching the service api
    api = client.resources.get(api_version="v1", kind="Service")

    try:
       namespace = input("\n\t -> Namespace: ")
       name = input("\t -> Name: ")

       # Deleting service `frontend-service` from the `default` namespace
       service_deleted = api.delete(name=name, body={}, namespace=namespace)
    except:
       print("\n[ERROR] something went wrong!")
    finally:
       print("\n[INFO] service `" + name + "` deleted\n")


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


if __name__ == "__main__":
    main()
