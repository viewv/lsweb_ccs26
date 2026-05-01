import { sequelize } from "../../database/db";
import { Session, SessionStatus } from "../../database/models/session";
import { Logging } from "../logging";
import * as zmq from "zeromq";

const ZMQ_HOST = process.env.ZMQ_HOST ? process.env.ZMQ_HOST : "tcp://127.0.0.1:5555";
const ZMQ_EXPERIMENT = process.env.ZMQ_EXPERIMENT ? process.env.ZMQ_EXPERIMENT : "cxss";
const CRAWLER_ID = process.env.CRAWLER_ID ? process.env.CRAWLER_ID : 0;


class ZMQWrapper {
    sock?: zmq.Request;
    sessionCount: number = 0;

    state: "session_request" | "session_unlock" | "none" = "none";
    unlockedSessionId: number = -1;

    /**
     * Initialize new ZMQ connection to ZMQ_HOST
     */
    async init() {
        this.sock = new zmq.Request();
        this.sock.connect(ZMQ_HOST)
        Logging.info("Initialized ZMQ Session")
    }

    /**
     * Request a session from the account network, sends the session_request or get_specific_session via ZMQ to the 
     * configured account framework endpoint.
     * 
     * @param site Optional site to request session for (if set, request type changes to get_specific_session)
     * @returns 
     */
    async getSession(site?: string) {
        if (!this.sock) {
            Logging.error(`ZMQ-Socket not initialized during call to get a new session.`)
            process.exit(-1);
        }
        const request = {
            "id": CRAWLER_ID,
            "type": site ? "get_specific_session" : "get_session",
            "experiment": ZMQ_EXPERIMENT,
            ...(site && { site })
        }
        this.state = "session_request";
        Logging.info("Requesting ZMQ session")
        await this.sock.send(JSON.stringify(request))
        // Parse the result
        const [result] = await this.sock.receive()
        const parsedResult = JSON.parse(result.toString());
        // Inspect success flag of response
        if (parsedResult.success) {
            // If success flag is set, it means we got a session and then we store it in the database
            const t = await sequelize.transaction();
            try {
                // Create session in databse if it does not exist
                const { session, session_data } = parsedResult;
                const { id } = session;

                // Check if session already exists
                let sessionInDb = await Session.findOne({
                    where: {
                        id: id
                    }, transaction: t
                })
                if (sessionInDb) {
                    // If it does exist, unlock? the existing session again
                    await Session.update({
                        session_status: SessionStatus.ACTIVE
                    }, {
                        where: {
                            id: id
                        },
                        transaction: t
                    })
                    Logging.warn("Setting an existing session to ACTIVE again due to okay from zmq connection.")
                } else {
                    // Create if it does not exist
                    sessionInDb = await Session.create({
                        id: id,
                        session_information: session,
                        session_data: session_data,
                        session_status: SessionStatus.ACTIVE
                    }, { transaction: t })
                }

                await t.commit();
                return sessionInDb;

            } catch (err: unknown) {
                Logging.error(`Failed to enter new session due to error. Error: ${(err as Error).toString()}`)
                await t.rollback();
            }
        } else {
            // If success was false, return/do nothing and output log message
            Logging.error(`Session request did not yield new session. success=false`)
        }
    }

    /**
     * Perform an unlock request on the ZMQ connection given the argument id, so it is marked as unused
     * by the current running experiment and can be redistributed. Also, the crawler does now ignore the 
     * session for in the future.
     * 
     * @param id session_id of Session to unlock
     */
    async unlockSession(id: number) {
        if (!this.sock) {
            Logging.error(`ZMQ-Socket not initialized during call to unlock`)
            process.exit(-1);
        }
        const request = {
            "id": CRAWLER_ID,
            "type": "unlock_session",
            "experiment": ZMQ_EXPERIMENT,
            "session_id": id
        }

        this.state = "session_unlock";
        this.unlockedSessionId = id;

        await this.sock.send(JSON.stringify(request));
        const [result] = await this.sock.receive();
        const parsedResult = JSON.parse(result.toString());

        if (parsedResult.success) {
            Logging.info(`Unlocking session successful. Session_ID: ${id}`)
            if (this.unlockedSessionId !== -1) {
                await Session.update({
                    session_status: SessionStatus.UNLOCKED,
                    additional_information: {
                        message: "Successfully unlocked from zmq connection (success=true)."
                    }
                }, {
                    where: {
                        id: this.unlockedSessionId
                    }
                })
            }
        } else {
            Logging.error(`Unlocking session failed.`)
        }
    }
}

export { ZMQWrapper };