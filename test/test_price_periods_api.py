import asyncio
import hashlib
import os
import unittest
from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase

from iikoserver_client import ApiClient, Configuration
from iikoserver_client.api.corporation_management_api import CorporationManagementApi
from iikoserver_client.api.price_periods_api import PricePeriodsApi
from iikoserver_client.api.session_management_api import SessionManagementApi
from iikoserver_client.models.period_schedule_dto import PeriodScheduleDto
from iikoserver_client.models.period_schedule_item_dto import PeriodScheduleItemDto


class TestPricePeriodsApi(IsolatedAsyncioTestCase):
    """Тестирование API управления периодами действия цен"""

    async def asyncSetUp(self) -> None:
        """Настройка перед каждым тестом"""
        # Read credentials from env variables or set them directly
        self.server_url = os.environ.get("IIKO_SERVER_URL", None)
        self.login = os.environ.get("IIKO_SERVER_LOGIN", None)  # Replace with your login
        self.password = os.environ.get("IIKO_SERVER_PASSWORD", None)  # Replace with your password
        self.password_hash = hashlib.sha1(self.password.encode()).hexdigest()
        
        # Create configuration
        self.config = Configuration(host=self.server_url, debug=True)
        
        # Create API client with context manager support
        self.client = ApiClient(configuration=self.config)
        self.session_api = SessionManagementApi(api_client=self.client)
        await self.session_api.auth_post(login=self.login, var_pass=self.password_hash)
        self.api = PricePeriodsApi(api_client=self.client)

        self.test_department_id = "65430fca-3116-f1b6-0197-5488678d0012"
        self.test_department_name = "Мой ресторан"

    async def asyncTearDown(self) -> None:
        """Очистка после каждого теста"""
        # Make sure to properly close all connections
        try:
            await self.session_api.logout_post()
        except Exception as e:
            print(f"Warning: logout failed: {e}")
        
        # Ensure client is closed properly
        await self.client.close()
        
        # Give event loop time to cleanup resources
        await asyncio.sleep(0.1)

    async def test_entities_period_schedules_get(self) -> None:
        """Тест получения списка расписаний периодов действия
        
        Тестирует получение всех расписаний периодов действия
        """
        try:
            result = await self.api.v2_entities_period_schedules_get(
                include_deleted=False,
                id=None,
                revision_from=-1
            )
            
            self.assertIsNotNone(result)
            self.assertEqual(result.result, "SUCCESS")
            self.assertIsInstance(result.response, list)
            self.assertIsInstance(result.revision, int)
            
            print(f"Retrieved {len(result.response)} period schedules")
            
            # Проверяем структуру расписаний
            for schedule in result.response:
                self.assertIsNotNone(schedule.id)
                self.assertIsNotNone(schedule.name)
                self.assertIsInstance(schedule.deleted, bool)
                self.assertIsInstance(schedule.periods, list)
                
                # Проверяем структуру периодов
                for period in schedule.periods:
                    self.assertIsNotNone(period.begin)
                    self.assertIsNotNone(period.end)
                    self.assertIsInstance(period.days_of_week, list)
                    
                    # Проверяем формат времени (HH:mm)
                    self.assertRegex(period.begin, r'^\d{2}:\d{2}$')
                    self.assertRegex(period.end, r'^\d{2}:\d{2}$')
                    
                    # Проверяем валидность дней недели (1-7)
                    for day in period.days_of_week:
                        self.assertIn(day, [1, 2, 3, 4, 5, 6, 7])
                        
        except Exception as e:
            self.fail(f"Period schedules list test failed with error: {str(e)}")

    
    async def test_entities_period_schedules_by_id_get(self) -> None:
        """Тест получения расписания периода действия по идентификатору
        
        Сначала получает список расписаний, затем запрашивает одно по ID
        """
        try:
            # Сначала получаем список расписаний
            list_result = await self.api.v2_entities_period_schedules_get(
                include_deleted=False
            )
            
            if not list_result.response or len(list_result.response) == 0:
                print("No period schedules found, skipping by_id test")
                return
            
            # Берем первое расписание из списка
            test_schedule_id = list_result.response[0].id
            
            result = await self.api.v2_entities_period_schedules_by_id_get(id=test_schedule_id)
            
            self.assertIsNotNone(result)
            self.assertEqual(result.id, test_schedule_id)
            self.assertIsNotNone(result.name)
            self.assertIsInstance(result.deleted, bool)
            self.assertIsInstance(result.periods, list)
            
            # Проверяем структуру периодов
            for period in result.periods:
                self.assertIsNotNone(period.begin)
                self.assertIsNotNone(period.end)
                self.assertIsInstance(period.days_of_week, list)
                
                # Проверяем формат времени (HH:mm)
                self.assertRegex(period.begin, r'^\d{2}:\d{2}$')
                self.assertRegex(period.end, r'^\d{2}:\d{2}$')
                
                # Проверяем валидность дней недели (1-7)
                for day in period.days_of_week:
                    self.assertIn(day, [1, 2, 3, 4, 5, 6, 7])
            
            print(f"Retrieved period schedule by ID: {test_schedule_id} - {result.name}")
            
        except Exception as e:
            self.fail(f"Period schedule by ID test failed with error: {str(e)}")


if __name__ == '__main__':
    unittest.main() 