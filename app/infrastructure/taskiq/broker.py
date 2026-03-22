from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker
from taskiq_fastapi import init as taskiq_fastapi_init
from app.infrastructure.config.config import Config
from taskiq.middlewares import SmartRetryMiddleware

config = Config()

result_backend = RedisAsyncResultBackend(
    redis_url=config.taskiq.taskiq_broker_url,
    result_ex_time=3600
)

broker = RedisStreamBroker(
    url=config.taskiq.taskiq_broker_url,
).with_result_backend(result_backend)

broker = broker.with_middlewares(
    SmartRetryMiddleware(
        default_retry_count=3,
        default_delay=5,
    )
)

taskiq_fastapi_init(broker, "main:app") 
from app.infrastructure.taskiq import tasks # noqa