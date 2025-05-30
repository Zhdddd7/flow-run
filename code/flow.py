# import requests
# from prefect import flow, task
# from prefect_docker.images import pull_docker_image
# from prefect.events import DeploymentEventTrigger
# from prefect.deployments.runner import DockerImage
# from prefect_docker.containers import (
#     create_docker_container,
#     start_docker_container,
#     get_docker_container_logs,
#     stop_docker_container,
#     remove_docker_container,
# )

# @task(name="get")
# async def get_timestamp_subflow() -> str:
#     # # 1) ensure the image is present
#     # await pull_docker_image("us-docker.pkg.dev/we-staging/test-app/get:latest")
#     # # 2) create & start
#     # container = await create_docker_container(image="us-docker.pkg.dev/we-staging/test-app/get:latest")
#     # await start_docker_container(container_id=container.id)
#     # # 3) fetch logs, clean up, and return
#     # logs = await get_docker_container_logs(container_id=container.id)
#     # await stop_docker_container(container_id=container.id)
#     # await remove_docker_container(container_id=container.id)
#     # return logs.decode().strip()
#     r = requests.get("http://34.122.35.150:8001/timestamp", timeout=10)
#     r.raise_for_status()
#     print(f"get: {r.json()}")
#     return r.json()["utc"]

# @task(name="convert")
# async def convert_to_pst_subflow(utc: str) -> str:
#     # # 1) ensure the image is present
#     # await pull_docker_image("us-docker.pkg.dev/we-staging/test-app/convert:latest")
#     # # 2) create & start
#     # container = await create_docker_container(image="us-docker.pkg.dev/we-staging/test-app/convert:latest", env={"INPUT_TIME": utc})
#     # await start_docker_container(container_id=container.id)
#     # # 3) fetch logs, clean up, and return
#     # logs = await get_docker_container_logs(container_id=container.id)
#     # await stop_docker_container(container_id=container.id)
#     # await remove_docker_container(container_id=container.id)
#     # return logs.decode().strip()
#     r = requests.post("http://104.198.71.120:8001/convert", json={"utc": utc}, timeout=10)
#     r.raise_for_status()
#     print(f"convert: {r.json()}")
#     return r.json()["pst"]

# @task
# def debug_env():
#     import os
#     prefs = {k: v for k, v in os.environ.items() if k.startswith("PREFECT_")}
#     print("PREFECT ENV:", prefs)


# @flow(name="process-image", log_prints=True)
# def process_image(image_path: str):
#     debug_env.submit()
#     ts = get_timestamp_subflow.submit()
#     pst = convert_to_pst_subflow.submit(ts)
#     result = pst.result()
#     print(f"Image {image_path} processed at PST {result}")

# if __name__ == "__main__":
#     process_image.deploy(
#         name="process-image",
#         work_pool_name="time-orch",
#         work_queue_name="queue-orch",
#         image=DockerImage(
#         name="us-docker.pkg.dev/we-staging/test-app/flow",
#         tag="latest",
#         # env={
#         #     "PREFECT_API_URL": "http://34.27.67.83:4200/api",
#         #     "PREFECT_API_AUTH_STRING": "admin:admin123",
#         # }
#         ),
#         job_variables={
#             "env": {
#                 "PREFECT_API_URL": "http://34.27.67.83:4200/api",
#                 "PREFECT_API_AUTH_STRING": "admin:admin123",
#             }
#         },
#         push=False,
#         build=False,
#         triggers=[
#             DeploymentEventTrigger(
#                 enabled=True,
#                 expect=["image.uploaded"],
#                 match={"prefect.resource.id": "image-uploader"},
#                 parameters={"image_path": "{{ event.details.image_path }}"},
#             )
#         ],
#     )




# flow.py using docker container to get utc and convert to pst, running on vm-a and vm-b
# flow.py
import docker
from pathlib import Path
from prefect import flow, task
from prefect.events import DeploymentEventTrigger
from prefect.deployments.runner import DockerImage


@task(name="get-utc", retries=1, retry_delay_seconds=5)
def get_utc() -> str:
    client = docker.from_env()
    c = client.containers.get("timestamp_daemon")
    exit_code, output = c.exec_run(["/usr/local/bin/get.py"])
    if exit_code != 0:
        raise RuntimeError(output.decode())
    return output.decode().strip()

@task(name="convert-pst", retries=1, retry_delay_seconds=5)
def convert_pst(utc: str) -> str:
    client = docker.from_env()
    c = client.containers.get("convert_daemon")
    exit_code, output = c.exec_run(["/usr/local/bin/convert.py", utc])
    if exit_code != 0:
        raise RuntimeError(output.decode())
    return output.decode().strip()

@flow(name="process-image", log_prints=True)
def process_image(image_path: str):
    utc = get_utc.submit()
    pst = convert_pst.submit(utc)
    print(f"Image {image_path} processed at PST {pst.result()}")

if __name__ == "__main__":
    # process_image.deploy(
    #     name="process-image",
    #     work_pool_name="time-orch",
    #     image=DockerImage(
    #     name="us-docker.pkg.dev/we-staging/test-app/flow",
    #     tag="latest",
    #     ),
    #     job_variables={
    #         "env": {
    #             "PREFECT_API_URL": "http://34.27.67.83:4200/api",
    #             "PREFECT_API_AUTH_STRING": "admin:admin123",
    #         }
    #     },
    #     push=False,
    #     build=False,
    #     triggers=[
    #         DeploymentEventTrigger(
    #             enabled=True,
    #             expect=["image.uploaded"],
    #             match={"prefect.resource.id": "image-uploader"},
    #             parameters={"image_path": "{{ event.details.image_path }}"},
    #         )
    #     ],
    # )
    process_image.from_source(
        source="git+https://github.com/Zhdddd7/flow-run.git@main",
        entrypoint="code/flow.py:process_image",
    ).deploy(
        name="process-image",
        work_pool_name="time-orch",
        image=DockerImage(                            
            name="us-docker.pkg.dev/we-staging/test-app/flow",
            tag="latest",
        ),
        push=False,
        build=False,
        triggers=[
            DeploymentEventTrigger(
                enabled=True,
                expect=["image.uploaded"],
                match={"prefect.resource.id": "image-uploader"},
                parameters={"image_path": "{{ event.details.image_path }}"},
            )
        ],
    )

