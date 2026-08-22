import random
import uuid
import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("codesense.simulator")

app = FastAPI(title="CodeSense Real-Time Data Simulator")

# Configuration
BACKEND_URL = "http://localhost:8000/api/v1/events"
BACKEND_BATCH_URL = "http://localhost:8000/api/v1/events/batch"

# Simulator State
class SimulatorState:
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self.current_scenario = "NORMAL"
        self.current_time = datetime.now(timezone.utc) - timedelta(days=30)  # Start 30 days ago to backfill
        self.tick_interval = 1.0  # seconds per tick in real time
        self.simulated_hours_per_tick = 1  # how many hours pass per tick
        self.seed = 42
        self.backend_url = BACKEND_URL
        self.backend_batch_url = BACKEND_BATCH_URL
        
        # In-memory entities for relational correlation
        self.org_id = "org-codesense-uuid"
        self.team_id = "team-platform-uuid"
        self.project_id = "proj-codesense-uuid"
        self.repository_id = "repo-backend-uuid"
        
        # Track active work items, PRs, builds, etc.
        self.active_work_items: Dict[str, Dict[str, Any]] = {}
        self.active_changes: Dict[str, Dict[str, Any]] = {}
        self.active_reviews: Dict[str, Dict[str, Any]] = {}
        self.active_builds: Dict[str, Dict[str, Any]] = {}
        self.active_deployments: Dict[str, Dict[str, Any]] = {}
        self.active_incidents: Dict[str, Dict[str, Any]] = {}
        
        # Lock for thread-safety
        self.lock = threading.Lock()

state = SimulatorState()

# Pydantic schemas for controls
class ScenarioUpdate(BaseModel):
    scenario: str

class ConfigUpdate(BaseModel):
    tick_interval: Optional[float] = None
    simulated_hours_per_tick: Optional[int] = None
    backend_url: Optional[str] = None


def generate_event(event_type: str, payload: Dict[str, Any], occurred_at: datetime) -> Dict[str, Any]:
    """Helper to structure a raw simulator event."""
    return {
        "provider": "simulator",
        "external_event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "event_timestamp": occurred_at.isoformat(),
        "payload": {
            "organization_external_id": state.org_id,
            "organization_name": "CodeSense Org",
            "team_external_id": state.team_id,
            "team_name": "Platform Team",
            "project_external_id": state.project_id,
            "project_name": "CodeSense Analytics Board",
            "repository_external_id": state.repository_id,
            "repository_name": "CodeSense Core",
            **payload
        },
        "source": "simulator"
    }


def send_events_to_backend(events: List[Dict[str, Any]]):
    """Sends a batch of events to the backend ingestion API."""
    if not events:
        return
    try:
        if len(events) == 1:
            url = state.backend_url
            resp = requests.post(url, json=events[0], timeout=5)
        else:
            url = state.backend_batch_url
            resp = requests.post(url, json=events, timeout=10)
        if resp.status_code not in (200, 201):
            logger.error(f"Backend returned error {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to post events to backend: {str(e)}")


def tick_simulation() -> List[Dict[str, Any]]:
    """Simulates 1 tick of activity and returns generated events."""
    events: List[Dict[str, Any]] = []
    
    with state.lock:
        state.current_time += timedelta(hours=state.simulated_hours_per_tick)
        curr_time = state.current_time
        scenario = state.current_scenario
        
        # Decide generation probabilities based on scenario
        work_item_creation_chance = 0.15
        work_item_start_chance = 0.20
        review_completion_chance = 0.40
        build_failure_chance = 0.05
        deploy_failure_chance = 0.05
        incident_creation_chance = 0.01
        
        if scenario == "HIGH_LOAD":
            work_item_creation_chance = 0.50
            work_item_start_chance = 0.40
        elif scenario == "REVIEW_BOTTLENECK":
            review_completion_chance = 0.02  # reviews stall
            work_item_creation_chance = 0.25
        elif scenario == "CI_BOTTLENECK":
            build_failure_chance = 0.60  # builds fail constantly
        elif scenario == "DEPLOYMENT_FAILURE":
            deploy_failure_chance = 0.60  # deployments fail constantly
        elif scenario == "INCIDENT_SPIKE":
            incident_creation_chance = 0.30  # lots of incidents
        elif scenario == "RECOVERY":
            # return to normal rates, and actively resolve outstanding incidents/reviews
            review_completion_chance = 0.80
            build_failure_chance = 0.02
            deploy_failure_chance = 0.02
            incident_creation_chance = 0.00
            
        # 1. Create Work Items
        if random.random() < work_item_creation_chance:
            wi_id = f"wi-{uuid.uuid4().hex[:8]}"
            wi_payload = {
                "work_item_id": wi_id,
                "item_type": random.choice(["BUG", "FEATURE", "TASK", "STORY"]),
                "title": f"Simulated Task {wi_id}",
                "status": "BACKLOG",
                "priority": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            }
            state.active_work_items[wi_id] = wi_payload
            events.append(generate_event("WORK_ITEM_CREATED", wi_payload, curr_time))

        # 2. Start Work Items -> Create Changes (PRs)
        pending_wis = [wi for wi in state.active_work_items.values() if wi["status"] == "BACKLOG"]
        if pending_wis and random.random() < work_item_start_chance:
            wi = random.choice(pending_wis)
            wi["status"] = "IN_PROGRESS"
            events.append(generate_event("WORK_ITEM_STARTED", {"work_item_id": wi["work_item_id"], "status": "IN_PROGRESS"}, curr_time))
            
            # Immediately open a corresponding Pull Request
            change_id = f"pr-{uuid.uuid4().hex[:8]}"
            change_payload = {
                "change_id": change_id,
                "work_item_id": wi["work_item_id"],
                "title": f"PR for {wi['title']}",
                "status": "OPEN",
                "additions": random.randint(10, 500),
                "deletions": random.randint(5, 200),
                "changed_files": random.randint(1, 15),
                "actor_ref": f"dev-{random.randint(1, 5)}@codesense.io",
            }
            state.active_changes[change_id] = change_payload
            events.append(generate_event("CHANGE_CREATED", change_payload, curr_time))
            
            # Immediately request a review
            review_id = f"rev-{uuid.uuid4().hex[:8]}"
            review_payload = {
                "review_id": review_id,
                "change_id": change_id,
                "status": "PENDING",
                "reviewer_reference": f"reviewer-{random.randint(1, 3)}@codesense.io",
            }
            state.active_reviews[change_id] = review_payload
            events.append(generate_event("REVIEW_REQUESTED", review_payload, curr_time))

        # 3. Complete Reviews -> Trigger Builds
        open_reviews = [rev for rev in state.active_reviews.values() if rev["status"] == "PENDING"]
        for rev in open_reviews:
            if random.random() < review_completion_chance:
                rev["status"] = "APPROVED"
                events.append(generate_event("REVIEW_COMPLETED", {"review_id": rev["review_id"], "change_id": rev["change_id"], "status": "APPROVED"}, curr_time))
                
                # Trigger a CI build for the approved PR
                build_id = f"build-{uuid.uuid4().hex[:8]}"
                build_payload = {
                    "build_id": build_id,
                    "change_id": rev["change_id"],
                    "status": "RUNNING",
                    "branch": "main",
                    "commit_sha": uuid.uuid4().hex[:16],
                }
                state.active_builds[build_id] = build_payload
                events.append(generate_event("BUILD_STARTED", build_payload, curr_time))

        # 4. Process Running Builds -> Complete Builds (Succeed or Fail)
        running_builds = [b for b in state.active_builds.values() if b["status"] == "RUNNING"]
        for b in running_builds:
            # Completes this tick
            failed = random.random() < build_failure_chance
            status_str = "FAILED" if failed else "SUCCESS"
            b["status"] = status_str
            
            payload = {
                "build_id": b["build_id"],
                "change_id": b["change_id"],
                "status": status_str,
                "duration_seconds": random.randint(60, 300) if not failed else random.randint(10, 90),
            }
            events.append(generate_event("BUILD_COMPLETED", payload, curr_time))
            if failed:
                events.append(generate_event("BUILD_FAILED", payload, curr_time))
            else:
                events.append(generate_event("BUILD_SUCCEEDED", payload, curr_time))
                
                # If build succeeded, start a Deployment
                dep_id = f"dep-{uuid.uuid4().hex[:8]}"
                dep_payload = {
                    "deployment_id": dep_id,
                    "change_id": b["change_id"],
                    "status": "RUNNING",
                    "environment": "PRODUCTION",
                }
                state.active_deployments[dep_id] = dep_payload
                events.append(generate_event("DEPLOYMENT_STARTED", dep_payload, curr_time))

        # 5. Process Deployments (Complete successfully, Fail, or Rollback)
        running_deps = [d for d in state.active_deployments.values() if d["status"] == "RUNNING"]
        for d in running_deps:
            failed = random.random() < deploy_failure_chance
            status_str = "FAILED" if failed else "SUCCESS"
            d["status"] = status_str
            
            payload = {
                "deployment_id": d["deployment_id"],
                "change_id": d["change_id"],
                "status": status_str,
                "environment": "PRODUCTION",
                "duration_seconds": random.randint(45, 180) if not failed else random.randint(5, 30),
            }
            events.append(generate_event("DEPLOYMENT_COMPLETED", payload, curr_time))
            if failed:
                events.append(generate_event("DEPLOYMENT_FAILED", payload, curr_time))
                # Trigger rollback event immediately
                events.append(generate_event("DEPLOYMENT_ROLLED_BACK", {**payload, "status": "ROLLED_BACK"}, curr_time))
            else:
                # Successfully completed! Clean up change & work item status
                change = state.active_changes.get(d["change_id"])
                if change:
                    change["status"] = "MERGED"
                    events.append(generate_event("CHANGE_MERGED", {"change_id": change["change_id"], "status": "MERGED"}, curr_time))
                    
                    wi = state.active_work_items.get(change["work_item_id"])
                    if wi:
                        wi["status"] = "COMPLETED"
                        events.append(generate_event("WORK_ITEM_COMPLETED", {"work_item_id": wi["work_item_id"], "status": "COMPLETED"}, curr_time))

        # 6. Incident Management
        if random.random() < incident_creation_chance:
            inc_id = f"inc-{uuid.uuid4().hex[:8]}"
            inc_payload = {
                "incident_id": inc_id,
                "title": f"Incident {inc_id} - Service degradation",
                "severity": random.choice(["SEV1", "SEV2", "SEV3"]),
                "status": "OPEN",
            }
            state.active_incidents[inc_id] = inc_payload
            events.append(generate_event("INCIDENT_CREATED", inc_payload, curr_time))
            
            # Immediately acknowledge
            inc_payload["status"] = "ACKNOWLEDGED"
            events.append(generate_event("INCIDENT_ACKNOWLEDGED", {**inc_payload, "status": "ACKNOWLEDGED"}, curr_time))

        # Under RECOVERY or normally, resolve some incidents
        active_incidents_list = [inc for inc in state.active_incidents.values() if inc["status"] in ("OPEN", "ACKNOWLEDGED")]
        resolve_chance = 0.50 if scenario == "RECOVERY" else 0.15
        for inc in active_incidents_list:
            if random.random() < resolve_chance:
                inc["status"] = "RESOLVED"
                events.append(generate_event("INCIDENT_RESOLVED", {"incident_id": inc["incident_id"], "status": "RESOLVED"}, curr_time))

    return events


def run_loop():
    """Main loop for the background simulator thread."""
    # First, backfill historical data (e.g. 30 days of data) to give DB baseline
    # Simulating 30 days * 24 hours = 720 ticks
    # We send them in batches of 10 ticks to make it super fast but realistic
    logger.info("Starting historical data backfill (30 days)...")
    backfill_ticks = 30 * 24
    batch: List[Dict[str, Any]] = []
    
    for i in range(backfill_ticks):
        events = tick_simulation()
        batch.extend(events)
        if len(batch) >= 100:
            send_events_to_backend(batch)
            batch = []
            
    if batch:
        send_events_to_backend(batch)
        
    logger.info("Backfill complete. Entering real-time simulation loop.")
    
    # Real-time streaming loop
    while True:
        with state.lock:
            if not state.is_running:
                break
            paused = state.is_paused
            interval = state.tick_interval
            
        if not paused:
            events = tick_simulation()
            send_events_to_backend(events)
            
        time.sleep(interval)


@app.post("/simulator/start")
def start_simulator(background_tasks: BackgroundTasks):
    with state.lock:
        if state.is_running:
            return {"message": "Simulator is already running"}
        state.is_running = True
        state.is_paused = False
        
    background_tasks.add_task(run_loop)
    return {"message": "Simulator started"}


@app.post("/simulator/stop")
def stop_simulator():
    with state.lock:
        if not state.is_running:
            return {"message": "Simulator is not running"}
        state.is_running = False
    return {"message": "Simulator stopped"}


@app.post("/simulator/pause")
def pause_simulator():
    with state.lock:
        if not state.is_running:
            raise HTTPException(status_code=400, detail="Simulator is not running")
        state.is_paused = True
    return {"message": "Simulator paused"}


@app.post("/simulator/resume")
def resume_simulator():
    with state.lock:
        if not state.is_running:
            raise HTTPException(status_code=400, detail="Simulator is not running")
        state.is_paused = False
    return {"message": "Simulator resumed"}


@app.get("/simulator/status")
def get_status():
    with state.lock:
        return {
            "is_running": state.is_running,
            "is_paused": state.is_paused,
            "current_scenario": state.current_scenario,
            "simulated_time": state.current_time.isoformat(),
            "active_entities": {
                "work_items": len(state.active_work_items),
                "changes": len(state.active_changes),
                "reviews": len(state.active_reviews),
                "builds": len(state.active_builds),
                "deployments": len(state.active_deployments),
                "incidents": len(state.active_incidents),
            }
        }


@app.post("/simulator/scenario")
def set_scenario(payload: ScenarioUpdate):
    valid_scenarios = [
        "NORMAL", "HIGH_LOAD", "REVIEW_BOTTLENECK", 
        "CI_BOTTLENECK", "DEPLOYMENT_FAILURE", 
        "INCIDENT_SPIKE", "RECOVERY"
    ]
    if payload.scenario not in valid_scenarios:
        raise HTTPException(status_code=400, detail=f"Invalid scenario. Choose from {valid_scenarios}")
        
    with state.lock:
        state.current_scenario = payload.scenario
    logger.info(f"Simulator scenario updated to: {payload.scenario}")
    return {"message": f"Scenario updated to {payload.scenario}"}


@app.post("/simulator/config")
def update_config(payload: ConfigUpdate):
    with state.lock:
        if payload.tick_interval is not None:
            state.tick_interval = payload.tick_interval
        if payload.simulated_hours_per_tick is not None:
            state.simulated_hours_per_tick = payload.simulated_hours_per_tick
        if payload.backend_url is not None:
            state.backend_url = payload.backend_url
    return {"message": "Configuration updated"}


@app.post("/simulator/tick")
def trigger_tick():
    """Manually triggers a simulated tick and returns generated events (useful for verification/tests)."""
    events = tick_simulation()
    return {"events_count": len(events), "events": events}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
