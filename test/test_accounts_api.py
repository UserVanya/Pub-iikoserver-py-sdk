import asyncio
import hashlib
import os
import unittest
from datetime import datetime, timedelta
from unittest import IsolatedAsyncioTestCase

from iikoserver_client import ApiClient, Configuration
from iikoserver_client.api.corporation_management_api import CorporationManagementApi
from iikoserver_client.api.accounts_api import AccountsApi
from iikoserver_client.api.session_management_api import SessionManagementApi
from iikoserver_client.models.account_dto import AccountDto
from iikoserver_client.models.account_type_enum import AccountTypeEnum


class TestAccountsApi(IsolatedAsyncioTestCase):
    """Тестирование API управления счетами"""

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
        self.api = AccountsApi(api_client=self.client)

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

    async def test_entities_accounts_list_get(self) -> None:
        """Тест получения списка счетов
        
        Тестирует получение всех счетов
        """
        try:
            result = await self.api.v2_entities_accounts_list_get(
                include_deleted=False,
                revision_from=-1
            )
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)
            
            print(f"Retrieved {len(result)} accounts")
            
            # Проверяем структуру счетов
            for account in result:
                self.assertIsInstance(account, AccountDto)
                self.assertIsNotNone(account.root_type)
                self.assertEqual(account.root_type, "Account")
                self.assertIsNotNone(account.id)
                self.assertIsNotNone(account.code)
                self.assertIsInstance(account.deleted, bool)
                self.assertIsNotNone(account.name)
                self.assertIsNotNone(account.type)
                self.assertIsInstance(account.system, bool)
                self.assertIsInstance(account.custom_transactions_allowed, bool)
                
                # Проверяем валидность типа счета
                self.assertIn(account.type, [
                    AccountTypeEnum.CASH,
                    AccountTypeEnum.ACCOUNTS_RECEIVABLE,
                    AccountTypeEnum.DEBTS_OF_EMPLOYEES,
                    AccountTypeEnum.CURRENT_ASSET,
                    AccountTypeEnum.OTHER_CURRENT_ASSET,
                    AccountTypeEnum.INVENTORY_ASSETS,
                    AccountTypeEnum.EMPLOYEES_LIABILITY,
                    AccountTypeEnum.ACCOUNTS_PAYABLE,
                    AccountTypeEnum.CLIENTS_LIABILITY,
                    AccountTypeEnum.OTHER_CURRENT_LIABILITY,
                    AccountTypeEnum.LONG_TERM_LIABILITY,
                    AccountTypeEnum.EQUITY,
                    AccountTypeEnum.COST_OF_GOODS_SOLD,
                    AccountTypeEnum.INCOME,
                    AccountTypeEnum.EXPENSES,
                    AccountTypeEnum.OTHER_INCOME,
                    AccountTypeEnum.OTHER_EXPENSES
                ])
                
                # account_parent_id и parent_corporate_id могут быть None
                if account.account_parent_id is not None:
                    self.assertIsInstance(account.account_parent_id, str)
                if account.parent_corporate_id is not None:
                    self.assertIsInstance(account.parent_corporate_id, str)
                    
        except Exception as e:
            self.fail(f"Accounts list test failed with error: {str(e)}")

    

if __name__ == '__main__':
    unittest.main() 