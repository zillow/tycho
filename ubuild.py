from uranium import current_build

current_build.config.set_defaults({
    "module": "event_tracking"
})

current_build.packages.install("../orbital-core", develop=True)
from orbital_core.build import bootstrap_build
bootstrap_build(current_build)

@build.task
def start_db(build):
    build.executables.run(["/bin/bash", "-c", (
        "docker run -p 27017:27017 --name tycho-db"
        " -d mongo"
    )])

@build.task
def stop_db(build):
    build.executables.run(["/bin/bash", "-c", "docker stop tycho-db"])
    build.executables.run(["/bin/bash", "-c", "docker rm tycho-db"])

# build.tasks.prepend("test", "start_mongodb_docker")
# build.tasks.append("test", "stop_mongodb_docker")
