import asyncio
import hashlib
import os
import unittest
from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase

from iikoserver_client import ApiClient, Configuration
from iikoserver_client.api.corporation_management_api import CorporationManagementApi
from iikoserver_client.api.price_categories_api import PriceCategoriesApi
from iikoserver_client.api.session_management_api import SessionManagementApi
from iikoserver_client.models.client_price_category_dto import ClientPriceCategoryDto
from iikoserver_client.models.pricing_strategy_type_enum import PricingStrategyTypeEnum


class TestPriceCategoriesApi(IsolatedAsyncioTestCase):
    """Тестирование API управления ценовыми категориями"""

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
        self.api = PriceCategoriesApi(api_client=self.client)

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

    async def test_entities_price_categories_get(self) -> None:
        """Тест получения списка ценовых категорий
        
        Тестирует получение всех ценовых категорий
        """
        try:
            result = await self.api.v2_entities_price_categories_get(
                include_deleted=False,
                id=None,
                revision_from=-1
            )
            
            self.assertIsNotNone(result)
            self.assertEqual(result.result, "SUCCESS")
            self.assertIsInstance(result.response, list)
            self.assertIsInstance(result.revision, int)
            
            print(f"Retrieved {len(result.response)} price categories")
            
            # Проверяем структуру ценовых категорий
            for category in result.response:
                self.assertIsNotNone(category.id)
                self.assertIsNotNone(category.name)
                self.assertIsInstance(category.deleted, bool)
                self.assertIsNotNone(category.code)
                self.assertIsInstance(category.assignable_manually, bool)
                self.assertIsNotNone(category.pricing_strategy)
                self.assertIsNotNone(category.pricing_strategy.type)
                
                # Проверяем валидность типа стратегии
                self.assertIn(category.pricing_strategy.type, [
                    PricingStrategyTypeEnum.ABSOLUTE_VALUE,
                    PricingStrategyTypeEnum.PERCENT
                ])
                
                # Проверяем наличие соответствующих полей в зависимости от типа стратегии
                if category.pricing_strategy.type == PricingStrategyTypeEnum.ABSOLUTE_VALUE:
                    self.assertIsNotNone(category.pricing_strategy.delta)
                elif category.pricing_strategy.type == PricingStrategyTypeEnum.PERCENT:
                    self.assertIsNotNone(category.pricing_strategy.percent)
                    
        except Exception as e:
            self.fail(f"Price categories list test failed with error: {str(e)}")

    
    async def test_entities_price_categories_by_id_get(self) -> None:
        """Тест получения ценовой категории по идентификатору
        
        Сначала получает список категорий, затем запрашивает одну по ID
        """
        try:
            # Сначала получаем список категорий
            list_result = await self.api.v2_entities_price_categories_get(
                include_deleted=False
            )
            
            if not list_result.response or len(list_result.response) == 0:
                print("No price categories found, skipping by_id test")
                return
            
            # Берем первую категорию из списка
            test_category_id = list_result.response[0].id
            
            result = await self.api.v2_entities_price_categories_by_id_get(id=test_category_id)
            
            self.assertIsNotNone(result)
            self.assertEqual(result.id, test_category_id)
            self.assertIsNotNone(result.name)
            self.assertIsNotNone(result.code)
            self.assertIsInstance(result.deleted, bool)
            self.assertIsInstance(result.assignable_manually, bool)
            self.assertIsNotNone(result.pricing_strategy)
            
            print(f"Retrieved price category by ID: {test_category_id} - {result.name}")
            
        except Exception as e:
            self.fail(f"Price category by ID test failed with error: {str(e)}")

    

if __name__ == '__main__':
    unittest.main() 