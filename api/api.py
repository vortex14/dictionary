from fastapi import Depends, FastAPI
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter


def get_x():
    return 10


app = FastAPI()
router = InferringRouter()  # Step 1: Create a router


@cbv(router)  # Step 2: Create and decorate a class to hold the endpoints
class Foo:
    # Step 3: Add dependencies as class attributes
    x: int = Depends(get_x)

    @router.get("/")
    def bar(self) -> int:
        # Step 4: Use `self.<dependency_name>` to access shared dependencies
        return self.x

    @app.on_event("shutdown")
    async def on_shutdown():
        print("close")
        pass

app.include_router(router)

