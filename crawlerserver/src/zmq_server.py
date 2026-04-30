import zmq
import json
import asyncio
from typing import Dict, Any

from config import Config

from tortoise.expressions import Q
from tortoise import timezone
from database.model.sites import Site
from database.db import init_db, close_db


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def locate_experiment(self, experiment: str):
        experiment_field = None
        experiment_state_field = None
        experiment_start_time_field = None
        experiment_end_time_field = None

        if experiment == "headers":
            experiment_field = "experiment_headers"
            experiment_state_field = "experiment_headers_state"
            experiment_start_time_field = "experiment_headers_start_time"
            experiment_end_time_field = "experiment_headers_end_time"
        elif experiment == "inclusions":
            experiment_field = "experiment_inclusions"
            experiment_state_field = "experiment_inclusions_state"
            experiment_start_time_field = "experiment_inclusions_start_time"
            experiment_end_time_field = "experiment_inclusions_end_time"
        elif experiment == "cxss":
            experiment_field = "experiment_cxss"
            experiment_state_field = "experiment_cxss_state"
            experiment_start_time_field = "experiment_cxss_start_time"
            experiment_end_time_field = "experiment_cxss_end_time"
        elif experiment == "pmsecurity":
            experiment_field = "experiment_pmsecurity"
            experiment_state_field = "experiment_pmsecurity_state"
            experiment_start_time_field = "experiment_pmsecurity_start_time"
            experiment_end_time_field = "experiment_pmsecurity_end_time"
        else:
            raise ValueError(f"Unsupported experiment type: {experiment}")

        return experiment_field, experiment_state_field, experiment_start_time_field, experiment_end_time_field

    async def get_session(self, crawler_id, experiment: str) -> Dict[str, Any]:
        # Ignore crawler_id for artifact review, just fetch any free site
        # This simplifies the process to automatically pick from the seeded database list

        # Step 1: Select the correct database fields based on the experiment parameter
        experiment_field, experiment_state_field, experiment_start_time_field, experiment_end_time_field = self.locate_experiment(
            experiment)

        # Step 2: Fetch the first available site with state 'free'
        site = await Site.filter(
            Q(**{experiment_state_field: "free"})
        ).first()

        if not site:
            return {
                "success": False,
                "message": "No free site found in the database."
            }

        # Step 3: Update the experiment's start time and set its state to 'process'
        current_time = timezone.now()
        setattr(site, experiment_start_time_field, current_time)
        setattr(site, experiment_state_field, "process")

        # Save changes to the database
        await site.save()

        # Step 4: Return the relevant session data
        return {
            "success": True,
            "site": site.site,
            "site_id": site.id,
            "url": site.url,
            "rank": site.rank,
            "experiment": experiment,
        }

    async def get_specific_session(self, id: int, experiment: str, rsite: str) -> Dict[str, Any]:
        # Step 1: Select the correct database fields based on the experiment parameter
        experiment_field, experiment_state_field, experiment_start_time_field, experiment_end_time_field = self.locate_experiment(
            experiment)

        # Step 2: Find a free site that matches the requested rsite (either by site name or url)
        site = await Site.filter(
            (Q(site=rsite) | Q(url=rsite)) & Q(
                **{experiment_state_field: "free"})
        ).first()

        if not site:
            return {
                "success": False,
                "message": f"No free site found matching {rsite}."
            }

        # Step 3: Update the experiment's start time and set its state to 'process'
        current_time = timezone.now()
        setattr(site, experiment_start_time_field, current_time)
        setattr(site, experiment_state_field, "process")

        # Save changes to the database
        await site.save()

        # Step 4: Return the relevant session data
        return {
            "success": True,
            "site": site.site,
            "site_id": site.id,
            "url": site.url,
            "rank": site.rank,
            "experiment": experiment,
        }

    async def unlock_session(self, experiment: str, session_id: int) -> bool:
        # Step 1: Select the correct database fields based on the experiment parameter
        experiment_field, experiment_state_field, experiment_start_time_field, experiment_end_time_field = self.locate_experiment(
            experiment)

        # Step 2: Locate the site by its session_id
        site = await Site.filter(id=session_id).first()

        if not site:
            return False  # Site not found, return false

        # Step 3: Update the experiment's end time and set its state to 'finished'
        current_time = timezone.now()
        setattr(site, experiment_state_field, "finished")
        setattr(site, experiment_end_time_field, current_time)

        # Save changes to the database
        await site.save()

        return True  # Update successful


def generate_session(response_data):
    session = {
        "session": {
            "id": response_data["site_id"],
            "website": {
                "url": response_data["url"],
                "site": response_data["site"],
                "rank": response_data["rank"],
            },
            "experiment": response_data["experiment"],
        }
    }
    return session


async def main():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(Config.ZMQ_SOCK)  # Adjust the port as needed

    await init_db()

    session_manager = SessionManager()

    def send_success(data):
        msg = {"success": True}
        msg.update(data)
        socket.send_string(json.dumps(msg, default=str))

    def send_error(error):
        socket.send_string(json.dumps({"success": False, "error": error}))

    print("Server started. Waiting for requests...")

    while True:
        try:
            message = socket.recv_string()
            request = json.loads(message)

            if request["type"] == "get_session":
                response_data = await session_manager.get_session(request["id"], request["experiment"])
                if response_data["success"]:
                    session = generate_session(response_data)
                    send_success(session)
                else:
                    send_error(response_data["message"])
                    continue

            elif request["type"] == "get_specific_session":
                response_data = await session_manager.get_specific_session(
                    request["id"], request["experiment"], request["site"])
                if response_data["success"]:
                    session = generate_session(response_data)
                    send_success(session)
                else:
                    send_error(response_data["message"])
                    continue

            elif request["type"] == "unlock_session":
                success = await session_manager.unlock_session(request["experiment"], request["session_id"])
                if success:
                    send_success({})
                else:
                    send_error("Session not found")
                continue

        except KeyboardInterrupt as e:
            print("Shutting down...")
            break
        except Exception as e:
            # We don't want the ZMQ server to stop working just because of a minor error
            print(f"ZMQ Server Error: {e}")
            send_error(f"ZMQ Server Error: {e}")

    socket.close()
    context.term()

    await close_db()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server interrupted. Cleaning up...")
