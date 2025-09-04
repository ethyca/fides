from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fides.api.models.detection_discovery.web_monitor import WebMonitorGroupJob


class TestWebMonitorGroupJob:
    async def test_create_web_monitor_group_job(self, async_session: AsyncSession):
        """Test creating a web monitor group job"""
        raw_data = {
            "https://example.com": {
                "us": {
                    "notices": [
                        {
                            "data_uses": ["essential"],
                            "notice_key": "essential-notice",
                            "mechanism": "notice_only",
                        },
                        {
                            "data_uses": ["analytics"],
                            "notice_key": "analytics-notice",
                            "mechanism": "opt_out",
                        },
                        {
                            "data_uses": ["marketing.advertising.third_party.targeted"],
                            "notice_key": "marketing-notice",
                            "mechanism": "opt_in",
                        },
                    ],
                    "is_tcf_experience": False,
                }
            }
        }
        processed_data = {
            "https://example.com": {
                "us": {
                    "essential": "notice_only",
                    "analytics": "opt_out",
                    "marketing.advertising.third_party.targeted": "opt_in",
                }
            }
        }
        web_monitor_group_job = await WebMonitorGroupJob.create_async(
            async_session,
            group_id="test_group_id",
            is_test_run=False,
            raw_experiences_data=raw_data,
            processed_experiences_data=processed_data,
        )
        assert web_monitor_group_job.group_id == "test_group_id"
        assert web_monitor_group_job.is_test_run == False
        assert web_monitor_group_job.raw_experiences_data == raw_data
        assert web_monitor_group_job.processed_experiences_data == processed_data

        # Retrieve from the database to test it was persisted
        retrieve_item_query = select(WebMonitorGroupJob).where(
            WebMonitorGroupJob.group_id == "test_group_id"
        )

        result = await async_session.execute(retrieve_item_query)
        retrieved_web_monitor_group_job = result.scalars().first()
        assert retrieved_web_monitor_group_job.group_id == "test_group_id"
        assert retrieved_web_monitor_group_job.is_test_run == False
        assert retrieved_web_monitor_group_job.raw_experiences_data == raw_data
        assert (
            retrieved_web_monitor_group_job.processed_experiences_data == processed_data
        )

    async def test_get_by_group_id(self, async_session: AsyncSession):
        """Test getting a web monitor group job by group id"""
        raw_data = {
            "https://example.com": {
                "us": {
                    "data_uses": ["essential"],
                    "is_tcf_experience": False,
                }
            }
        }
        processed_data = {
            "https://example.com": {"us": {}},
        }
        await WebMonitorGroupJob.create_async(
            async_session,
            group_id="test_group_id",
            is_test_run=True,
            raw_experiences_data=raw_data,
            processed_experiences_data=processed_data,
        )
        retrieved_web_monitor_group_job = (
            await WebMonitorGroupJob.get_by_group_id_async(
                async_session, "test_group_id"
            )
        )

        assert retrieved_web_monitor_group_job.group_id == "test_group_id"
        assert retrieved_web_monitor_group_job.is_test_run == True
        assert retrieved_web_monitor_group_job.raw_experiences_data == raw_data
        assert (
            retrieved_web_monitor_group_job.processed_experiences_data == processed_data
        )
