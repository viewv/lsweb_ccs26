import zmq
import json
import argparse
import sys

ZMQ_ADDRESS = "tcp://localhost:5555"  # Fixed ZMQ address


def send_request(socket, request):
    socket.send_string(json.dumps(request))
    response = json.loads(socket.recv_string())
    return response


def get_session(socket, experiment):
    request = {
        "id": 0,
        "type": "get_session",
        "experiment": experiment
    }
    return send_request(socket, request)


def get_specific_session(socket, experiment, site):
    request = {
        "id": 0,
        "type": "get_specific_session",
        "experiment": experiment,
        "site": site
    }
    return send_request(socket, request)


def unlock_session(socket, session_id, experiment):
    request = {
        "id": 0,
        "type": "unlock_session",
        "experiment": experiment,
        "session_id": session_id
    }
    return send_request(socket, request)


def main(experiment):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(ZMQ_ADDRESS)

    try:
        # Test get_session
        print("Testing get_session...")
        response = get_session(socket, experiment)
        if response["success"]:
            print(f"Got session: {json.dumps(response['session'], indent=2)}")
            session_id = response['session']['id']
        else:
            print(f"Failed to get session: {
                  response.get('error', 'Unknown error')}")
            return

        # Test get_specific_session
        print("\nTesting get_specific_session...")
        specific_site = "facebook.com"
        response = get_specific_session(socket, experiment, specific_site)
        if response["success"]:
            print(f"Got specific session for {specific_site}: {
                  json.dumps(response['session'], indent=2)}")
        else:
            print(f"Failed to get specific session: {
                  response.get('error', 'Unknown error')}")

        # Test unlock_session
        print("\nTesting unlock_session...")
        response = unlock_session(socket, session_id, experiment)
        if response["success"]:
            print(f"Successfully unlocked session {session_id}")
        else:
            print(f"Failed to unlock session: {
                  response.get('error', 'Unknown error')}")

        # Test getting multiple sessions
        print("\nTesting multiple get_session calls...")
        for _ in range(5):
            response = get_session(socket, experiment)
            if response["success"]:
                print(f"Got session for site: {
                      response['session']['website']['site']}")
                print(response)
            else:
                print(f"Failed to get session: {
                      response.get('error', 'Unknown error')}")
                print(response)

    except zmq.ZMQError as e:
        print(f"ZMQ Error: {e}")
    except Exception as e:
        print(e)
        print(f"Unexpected error: {e}")
    finally:
        socket.close()
        context.term()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ZMQ Test Client")
    parser.add_argument("-e", "--experiment", type=str,
                        required=True, help="experiment name")
    args = parser.parse_args()

    sys.exit(main(args.experiment))
