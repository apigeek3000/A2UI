# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os

import click
import firebase_admin
from firebase_admin import auth, credentials
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2ui.a2ui_extension import get_a2ui_agent_extension
from agent import RestaurantAgent
from agent_executor import RestaurantAgentExecutor
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
try:
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
except Exception as e:
    logger.warning(
        f"Failed to initialize Firebase Admin SDK: {e}. Auth checks may fail if not configured properly with GOOGLE_APPLICATION_CREDENTIALS."
    )


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        # Public paths
        if request.url.path.endswith(
            "/.well-known/agent-card.json"
        ) or request.url.path.startswith("/static"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"error": "Unauthorized: Missing or invalid Authorization header"},
                status_code=401,
            )

        token = auth_header.split(" ")[1]
        try:
            # Verify the token
            decoded_token = auth.verify_id_token(token)
            request.state.user = decoded_token

            # Log the user email
            email = decoded_token.get("email")
            if email:
                logger.info(f"Request authenticated for user: {email}")
            else:
                logger.info("Request authenticated (no email found in token)")

        except Exception as e:
            logger.error(f"Auth error: {e}")
            return JSONResponse(
                {"error": "Unauthorized: Invalid token"}, status_code=401
            )

        return await call_next(request)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10002)
def main(host, port):
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "TRUE":
            if not os.getenv("GEMINI_API_KEY"):
                raise MissingAPIKeyError(
                    "GEMINI_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
                )

        capabilities = AgentCapabilities(
            streaming=True,
            extensions=[get_a2ui_agent_extension()],
        )
        skill = AgentSkill(
            id="find_restaurants",
            name="Find Restaurants Tool",
            description="Helps find restaurants based on user criteria (e.g., cuisine, location).",
            tags=["restaurant", "finder"],
            examples=["Find me the top 10 chinese restaurants in the US"],
        )

        base_url = f"http://{host}:{port}"

        agent_card = AgentCard(
            name="Restaurant Agent",
            description="This agent helps find restaurants based on user criteria.",
            url=base_url,  # <-- Use base_url here
            version="1.0.0",
            default_input_modes=RestaurantAgent.SUPPORTED_CONTENT_TYPES,
            default_output_modes=RestaurantAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        agent_executor = RestaurantAgentExecutor(base_url=base_url)

        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )
        import uvicorn

        app = server.build()

        app.add_middleware(FirebaseAuthMiddleware)

        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"http://localhost:\d+",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.mount("/static", StaticFiles(directory="images"), name="static")

        uvicorn.run(app, host=host, port=port)
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
