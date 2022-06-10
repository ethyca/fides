def test_create_task(celery_app, celery_worker):
    @celery_app.task
    def multiply(x, y):
        return x * y

    # Force `celery_app` to register our new task
    # See: https://github.com/celery/celery/issues/3642#issuecomment-369057682
    celery_worker.reload()
    assert multiply.run(4, 4) == 16
    assert multiply.delay(4, 4).get(timeout=10) == 16
