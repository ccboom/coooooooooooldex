# paradex_trader_async.py
# -*- coding: utf-8 -*-
"""
Paradex 交易操作类（异步版本）
包含所有交易相关的函数
"""

from playwright.async_api import Page, expect
import asyncio
from typing import Tuple, Optional, List, Dict
import re


class ParadexTrader:
    """Paradex 交易操作类（异步版本）"""

    def __init__(self, page: Page):
        self.page = page

    async def wait_for_page_ready(self, timeout: int = 30000) -> bool:
        """
        等待页面关键元素加载完成

        Args:
            timeout: 超时时间（毫秒）

        Returns:
            bool: 是否加载成功
        """
        try:
            print("等待页面加载...")

            await self.page.wait_for_selector(
                '[role="grid"][aria-readonly="true"]',
                state="visible",
                timeout=timeout
            )

            await self.page.wait_for_selector(
                'form[aria-label="Order Form"]',
                state="visible",
                timeout=timeout
            )

            await self.page.wait_for_selector(
                '[aria-label="Market Info"]',
                state="visible",
                timeout=timeout
            )

            await asyncio.sleep(2)

            print("✓ 页面加载完成")
            return True

        except Exception as e:
            print(f"✗ 页面加载超时: {e}")
            return False

    def extract_price_from_label(self, aria_label: str) -> Optional[float]:
        """
        从 aria-label 中提取价格

        Args:
            aria_label: 如 "Bid @ 95,000" 或 "Ask @ -"

        Returns:
            float: 提取的价格，如果无效返回 None
        """
        try:
            parts = aria_label.split('@')
            if len(parts) < 2:
                return None

            price_str = parts[1].strip()

            if price_str == '-' or price_str == '' or price_str == 'None':
                return None

            price_str = re.sub(r'[^\d.]', '', price_str)

            if not price_str:
                return None

            price = float(price_str)

            if price <= 0 or price > 10000000:
                return None

            return price

        except (ValueError, AttributeError):
            return None

    async def get_highest_bid_price(self, max_attempts: int = 3) -> Optional[float]:
        """
        获取订单簿中的最高买价（Bid）

        Args:
            max_attempts: 最大尝试次数

        Returns:
            float: 最高买价，如果获取失败返回 None
        """
        for attempt in range(max_attempts):
            try:
                print(f"尝试获取最高买价 (第 {attempt + 1}/{max_attempts} 次)...")

                await self.page.wait_for_selector(
                    '[aria-label*="Bid @"]',
                    state="visible",
                    timeout=10000
                )

                await asyncio.sleep(1)

                bid_elements = self.page.locator('[aria-label*="Bid @"]')
                count = await bid_elements.count()

                print(f"  找到 {count} 个买单")

                if count == 0:
                    print("  未找到买单，重试...")
                    await asyncio.sleep(1)
                    continue

                for i in range(count):
                    element = bid_elements.nth(i)
                    aria_label = await element.get_attribute('aria-label')

                    price = self.extract_price_from_label(aria_label)

                    if price is not None:
                        print(f"✓ 最高买价 (Bid): {price}")
                        return price

                print("  所有买单都无效，重试...")
                await asyncio.sleep(1)

            except Exception as e:
                print(f"  获取买价出错: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)

        print(f"✗ 获取最高买价失败")
        return None

    async def get_lowest_ask_price(self, max_attempts: int = 3) -> Optional[float]:
        """
        获取订单簿中的最低卖价（Ask）

        Args:
            max_attempts: 最大尝试次数

        Returns:
            float: 最低卖价，如果获取失败返回 None
        """
        for attempt in range(max_attempts):
            try:
                print(f"尝试获取最低卖价 (第 {attempt + 1}/{max_attempts} 次)...")

                await self.page.wait_for_selector(
                    '[aria-label*="Ask @"]',
                    state="visible",
                    timeout=10000
                )

                await asyncio.sleep(1)

                ask_elements = self.page.locator('[aria-label*="Ask @"]')
                count = await ask_elements.count()

                print(f"  找到 {count} 个卖单")

                if count == 0:
                    print("  未找到卖单，重试...")
                    await asyncio.sleep(1)
                    continue

                for i in range(count - 1, -1, -1):
                    element = ask_elements.nth(i)
                    aria_label = await element.get_attribute('aria-label')

                    price = self.extract_price_from_label(aria_label)

                    if price is not None:
                        print(f"✓ 最低卖价 (Ask): {price}")
                        return price

                print("  所有卖单都无效，重试...")
                await asyncio.sleep(1)

            except Exception as e:
                print(f"  获取卖价出错: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)

        print(f"✗ 获取最低卖价失败")
        return None

    def calculate_mid_price(self, bid: float, ask: float) -> float:
        """
        计算买卖价的中间价

        Args:
            bid: 买价
            ask: 卖价

        Returns:
            float: 中间价（保留1位小数）
        """
        mid_price = round((bid + ask) / 2, 1)
        spread = ask - bid
        spread_pct = (spread / bid) * 100

        print(f"✓ 买价: {bid}, 卖价: {ask}")
        print(f"✓ 价差: {spread:.2f} ({spread_pct:.3f}%)")
        print(f"✓ 中间价: {mid_price}")

        return mid_price

    async def set_order_side(self, side: str) -> bool:
        """
        设置订单方向（做多/做空）

        Args:
            side: "BUY" 或 "SELL"

        Returns:
            bool: 操作是否成功
        """
        try:
            side = side.upper()
            if side not in ["BUY", "SELL"]:
                print(f"✗ 无效的订单方向: {side}")
                return False

            # 查找订单方向选择器
            side_radio_group = self.page.locator('[role="radiogroup"][aria-label="Order Side"]')

            if await side_radio_group.count() == 0:
                print("✗ 未找到订单方向选择器")
                return False

            # 查找对应的按钮
            side_button = side_radio_group.locator(f'button[value="{side}"]')

            if await side_button.count() == 0:
                print(f"✗ 未找到 {side} 按钮")
                return False

            # 检查是否已选中
            if await side_button.get_attribute('aria-checked') == 'true':
                side_text = "做多" if side == "BUY" else "做空"
                print(f"✓ 已选择 {side_text}")
                return True

            # 点击按钮
            await side_button.click()
            await asyncio.sleep(0.3)

            side_text = "做多" if side == "BUY" else "做空"
            print(f"✓ 已切换到 {side_text}")
            return True

        except Exception as e:
            print(f"✗ 设置订单方向失败: {e}")
            return False

    async def click_market_order_tab(self) -> bool:
        """
        点击市价订单标签

        Returns:
            bool: 操作是否成功
        """
        try:
            market_button = self.page.locator(
                'button[role="tab"][id*="trigger-MARKET"]'
            )

            await expect(market_button).to_be_visible(timeout=5000)

            if await market_button.get_attribute('aria-selected') == 'true':
                print("✓ 已在市价订单标签")
                return True

            await market_button.click()

            await self.page.wait_for_selector(
                'div[role="tabpanel"][id*="MARKET"][data-state="active"]',
                state="visible",
                timeout=5000
            )

            await asyncio.sleep(0.5)

            print("✓ 已切换到市价订单")
            return True

        except Exception as e:
            print(f"✗ 切换到市价订单失败: {e}")
            return False

    async def click_limit_order_tab(self) -> bool:
        """
        点击限价订单标签

        Returns:
            bool: 操作是否成功
        """
        try:
            limit_button = self.page.locator(
                'button[role="tab"][id*="trigger-LIMIT"]'
            )

            await expect(limit_button).to_be_visible(timeout=5000)

            if await limit_button.get_attribute('aria-selected') == 'true':
                print("✓ 已在限价订单标签")
                return True

            await limit_button.click()

            await self.page.wait_for_selector(
                'div[role="tabpanel"][id*="LIMIT"][data-state="active"]',
                state="visible",
                timeout=5000
            )

            await asyncio.sleep(0.5)

            print("✓ 已切换到限价订单")
            return True

        except Exception as e:
            print(f"✗ 切换到限价订单失败: {e}")
            return False

    async def input_limit_price(self, price: float) -> bool:
        """
        在限价订单中输入价格

        Args:
            price: 要输入的价格

        Returns:
            bool: 操作是否成功
        """
        try:
            limit_panel = self.page.locator(
                'div[role="tabpanel"][id*="LIMIT"][data-state="active"]'
            )
            await expect(limit_panel).to_be_visible(timeout=5000)

            price_input = limit_panel.locator('input[inputmode="decimal"]').first

            await expect(price_input).to_be_visible(timeout=5000)
            await expect(price_input).to_be_editable(timeout=5000)

            await price_input.focus()
            await asyncio.sleep(0.2)
            await price_input.press('Control+A')
            await asyncio.sleep(0.1)
            await price_input.type(str(price), delay=50)
            await asyncio.sleep(0.1)
            await price_input.press('Tab')

            await asyncio.sleep(0.3)
            input_value = await price_input.input_value()
            print(f"✓ 已输入限价: {price} (框内值: {input_value})")

            return True

        except Exception as e:
            print(f"✗ 输入限价失败: {e}")
            return False

    async def input_order_size(self, size: float) -> bool:
        """
        输入订单大小

        Args:
            size: 订单大小

        Returns:
            bool: 操作是否成功
        """
        try:
            print(f"准备输入订单大小: {size}")

            # 方法1：在当前激活的面板中查找
            active_panel = self.page.locator('div[role="tabpanel"][data-state="active"]').first

            if await active_panel.count() > 0:
                print('daxiaoshuru')
                size_input = active_panel.locator('input[placeholder="大小"]').first

                # 如果找不到，尝试通过 inputmode 属性查找
                if await size_input.count() == 0:
                    print("  尝试备用选择器...")
                    size_input = active_panel.locator('input[inputmode="decimal"]').last
            else:
                # 如果没有找到激活面板，直接查找
                print('backup')
                size_input = self.page.locator('input[placeholder="大小"]').first

            await expect(size_input).to_be_visible(timeout=5000)
            await expect(size_input).to_be_editable(timeout=5000)

            # 先点击获得焦点
            await size_input.click()
            await asyncio.sleep(0.3)

            # 使用 fill 方法（推荐方式）
            # await size_input.fill('')  # 先清空
            # await asyncio.sleep(0.2)
            # await size_input.fill(str(size))  # 再填充
            # await asyncio.sleep(0.3)
            #
            # # 验证输入
            actual_value = await size_input.input_value()
            print(f"  第一次尝试结果: {actual_value}")

            # 如果失败，尝试第二种方法
            if actual_value == '0' or actual_value == '' or actual_value != str(size):
                print("  第一种方法失败，尝试第二种方法...")

                await size_input.click()
                await asyncio.sleep(0.2)

                # 使用键盘清空
                await size_input.press('Control+A')
                await asyncio.sleep(0.1)
                await size_input.press('Backspace')
                await asyncio.sleep(0.2)

                # 逐字符输入
                await size_input.type(str(size), delay=100)
                await asyncio.sleep(0.3)

                actual_value = await size_input.input_value()
                print(f"  第二次尝试结果: {actual_value}")

            # 触发失焦事件
            await size_input.press('Tab')
            await asyncio.sleep(0.2)

            # 最终验证
            actual_value = await size_input.input_value()
            print(f"✓ 已输入订单大小: {size} (框内值: {actual_value})")

            if actual_value == '0' or actual_value == '':
                print("  检测到输入失败，尝试备用方法...")
                return await self._input_order_size_backup(size)

            return True

        except Exception as e:
            print(f"✗ 输入订单大小失败: {e}")
            return await self._input_order_size_backup(size)

    async def _input_order_size_backup(self, size: float) -> bool:
        """
        备用方法：使用多种方式尝试输入

        Args:
            size: 订单大小

        Returns:
            bool: 操作是否成功
        """
        try:
            print("  使用备用输入方法...")

            # 尝试在激活面板中查找
            active_panel = self.page.locator('div[role="tabpanel"][data-state="active"]').first

            if await active_panel.count() > 0:
                size_input = active_panel.locator('input[placeholder="大小"]').first
                if await size_input.count() == 0:
                    size_input = active_panel.locator('input[inputmode="decimal"]').last
            else:
                size_input = self.page.locator('input[placeholder="大小"]').first

            # 方法1: JavaScript 强制设置
            print("  尝试 JavaScript 方法...")
            await size_input.evaluate(f'''
                (element) => {{
                    element.value = '{size}';
                    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    element.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                }}
            ''')

            await asyncio.sleep(0.5)
            actual_value = await size_input.input_value()
            print(f"  JavaScript 方法结果: {actual_value}")

            if actual_value != '0' and actual_value != '':
                print(f"✓ JavaScript 方法成功: {actual_value}")
                return True

            # 方法2: 点击后逐个删除再输入
            print("  尝试逐字符输入方法...")
            await size_input.click()
            await asyncio.sleep(0.2)

            # 多次按删除键确保清空
            for _ in range(10):
                await size_input.press('Backspace')
                await asyncio.sleep(0.05)

            for _ in range(10):
                await size_input.press('Delete')
                await asyncio.sleep(0.05)

            await asyncio.sleep(0.2)

            # 逐字符输入
            size_str = str(size)
            for char in size_str:
                await size_input.press(char)
                await asyncio.sleep(0.15)

            await asyncio.sleep(0.5)

            # 触发事件
            await size_input.press('Enter')
            await asyncio.sleep(0.2)

            actual_value = await size_input.input_value()
            print(f"  逐字符方法结果: {actual_value}")

            if actual_value != '0' and actual_value != '':
                print(f"✓ 逐字符方法成功: {actual_value}")
                return True

            # 方法3: 使用剪贴板
            print("  尝试剪贴板方法...")
            await size_input.click()
            await asyncio.sleep(0.2)

            # 使用 JavaScript 设置剪贴板并粘贴
            await self.page.evaluate(f'''
                async () => {{
                    await navigator.clipboard.writeText('{size}');
                }}
            ''')
            await asyncio.sleep(0.2)

            await size_input.press('Control+A')
            await asyncio.sleep(0.1)
            await size_input.press('Control+V')
            await asyncio.sleep(0.5)

            actual_value = await size_input.input_value()
            print(f"  剪贴板方法结果: {actual_value}")

            if actual_value != '0' and actual_value != '':
                print(f"✓ 剪贴板方法成功: {actual_value}")
                return True

            print(f"✗ 所有备用方法都失败了")
            return False

        except Exception as e:
            print(f"✗ 备用方法也失败: {e}")
            return False

    async def click_confirm_order(self, side: str = "BUY") -> bool:
        """
        点击确认订单按钮

        Args:
            side: "BUY" 或 "SELL"

        Returns:
            bool: 操作是否成功
        """
        try:
            # 根据方向选择不同的按钮文本
            if side.upper() == "BUY":
                button_text = "确认购买"
            else:
                button_text = "确认卖出"

            confirm_button = self.page.locator(
                f'button[type="submit"]:has-text("{button_text}")'
            )

            # 如果找不到，尝试通用的提交按钮
            if await confirm_button.count() == 0:
                confirm_button = self.page.locator('button[type="submit"]').first

            await expect(confirm_button).to_be_visible(timeout=5000)
            await expect(confirm_button).to_be_enabled(timeout=5000)

            await confirm_button.scroll_into_view_if_needed()
            await asyncio.sleep(0.3)

            await confirm_button.click()

            actual_text = (await confirm_button.text_content()).strip()
            print(f"✓ 已点击 {actual_text}")

            await asyncio.sleep(1)

            return True

        except Exception as e:
            print(f"✗ 点击确认按钮失败: {e}")
            return False

    async def wait_for_order_confirmation(self, timeout: int = 10) -> bool:
        """
        等待并验证订单是否成功提交到未结订单列表

        Args:
            timeout: 超时时间（秒）

        Returns:
            bool: 是否找到新订单
        """
        try:
            print("\n等待订单确认...")

            await asyncio.sleep(2)

            open_orders_tab = self.page.locator(
                'button[role="tab"][id*="trigger-open-orders"]'
            )

            await expect(open_orders_tab).to_be_visible(timeout=5000)
            await open_orders_tab.click()

            print("✓ 已切换到未结订单标签")
            await asyncio.sleep(1)

            orders_panel = self.page.locator(
                'div[role="tabpanel"][id*="open-orders"][data-state="active"]'
            )
            await expect(orders_panel).to_be_visible(timeout=5000)

            table_rows = orders_panel.locator('tbody tr')

            import time
            end_time = time.time() + timeout
            while time.time() < end_time:
                row_count = await table_rows.count()

                if row_count > 0:
                    print(f"✓ 找到 {row_count} 个未结订单")

                    for i in range(min(row_count, 3)):
                        row = table_rows.nth(i)
                        try:
                            cells = row.locator('td')
                            if await cells.count() >= 3:
                                market = (await cells.nth(0).text_content()).strip()
                                order_type = (await cells.nth(1).text_content()).strip()
                                size = (await cells.nth(2).text_content()).strip()
                                print(f"  订单 {i + 1}: {market} | {order_type} | {size}")
                        except:
                            pass

                    return True

                empty_message = orders_panel.locator('text=/无数据|No data|Empty/i')
                if await empty_message.count() > 0:
                    print("✗ 未结订单列表为空")
                    return False

                print(f"  等待订单出现... ({int(end_time - time.time())}秒剩余)")
                await asyncio.sleep(1)

            print("✗ 超时：未在未结订单中找到新订单")
            return False

        except Exception as e:
            print(f"✗ 验证订单失败: {e}")
            return False

    async def check_open_orders_exist(self) -> Tuple[bool, int]:
        """
        检查未结订单标签下是否有订单

        Returns:
            Tuple[bool, int]: (是否有订单, 订单数量)
        """
        try:
            print("\n检查未结订单...")

            open_orders_tab = self.page.locator(
                'button[role="tab"]:has-text("未结订单")'
            )

            if await open_orders_tab.count() == 0:
                print("✗ 未找到未结订单标签")
                return False, 0

            await open_orders_tab.click()
            await asyncio.sleep(1)

            orders_panel = self.page.locator(
                'div[role="tabpanel"][id="open-orders"]'
            )

            if not await orders_panel.is_visible():
                print("✗ 未结订单面板不可见")
                return False, 0

            table_rows = orders_panel.locator('tbody tr')
            row_count = await table_rows.count()

            if row_count > 0:
                print(f"✓ 找到 {row_count} 个未结订单")
                return True, row_count

            print("✓ 未结订单列表为空")
            return False, 0

        except Exception as e:
            print(f"✗ 检查订单失败: {e}")
            return False, 0

    async def verify_order_in_positions(self, timeout: int = 10) -> bool:
        """
        验证订单是否出现在持仓中（适用于市价单立即成交的情况）

        Args:
            timeout: 超时时间（秒）

        Returns:
            bool: 是否找到持仓
        """
        try:
            print("\n检查持仓变化...")

            positions_tab = self.page.locator(
                'button[role="tab"]:has-text("位置"), button[role="tab"]:has-text("持仓")'
            ).first

            if await positions_tab.count() == 0:
                print("✗ 未找到持仓标签")
                return False

            await positions_tab.click()
            await asyncio.sleep(1)

            positions_panel = self.page.locator(
                'div[role="tabpanel"][id="open-positions"]'
            )

            if not await positions_panel.is_visible():
                print("✗ 持仓面板不可见")
                return False

            import time
            end_time = time.time() + timeout
            while time.time() < end_time:
                table_rows = positions_panel.locator('tbody tr')
                row_count = await table_rows.count()

                if row_count > 0:
                    print(f"✓ 找到 {row_count} 个持仓")

                    try:
                        first_row = table_rows.first
                        cells = first_row.locator('td')
                        if await cells.count() >= 3:
                            market = (await cells.nth(0).text_content()).strip()
                            side = (await cells.nth(1).text_content()).strip()
                            size = (await cells.nth(2).text_content()).strip()
                            print(f"  最新持仓: {market} | {side} | {size}")
                    except:
                        pass

                    return True

                print(f"  等待持仓出现... ({int(end_time - time.time())}秒剩余)")
                await asyncio.sleep(1)

            print("✗ 超时：未找到持仓")
            return False

        except Exception as e:
            print(f"✗ 验证持仓失败: {e}")
            return False

    async def get_current_positions(self) -> List[Dict]:
        """
        获取当前所有持仓信息

        Returns:
            list: 持仓列表，每个元素包含 {market, side, size, row_index}
        """
        try:
            print("\n获取当前持仓...")

            positions_tab = self.page.locator(
                'button[role="tab"]:has-text("位置")'
            ).first

            if await positions_tab.count() == 0:
                print("✗ 未找到持仓标签")
                return []

            if await positions_tab.get_attribute('aria-selected') != 'true':
                await positions_tab.click()
                await asyncio.sleep(1)

            positions_panel = self.page.locator(
                'div[role="tabpanel"][id="open-positions"]'
            )

            if not await positions_panel.is_visible():
                print("✗ 持仓面板不可见")
                return []

            table_rows = positions_panel.locator('tbody tr')
            row_count = await table_rows.count()

            if row_count == 0:
                print("✓ 当前无持仓")
                return []

            positions = []

            for i in range(row_count):
                try:
                    row = table_rows.nth(i)
                    cells = row.locator('td')

                    if await cells.count() < 3:
                        continue

                    market_cell = cells.nth(0)
                    market = (await market_cell.locator('a').text_content()).strip()

                    side_cell = cells.nth(1)
                    side = (await side_cell.text_content()).strip()

                    size_cell = cells.nth(2)
                    size = (await size_cell.text_content()).strip()

                    position = {
                        'market': market,
                        'side': side,
                        'size': size,
                        'row_index': i
                    }

                    positions.append(position)
                    print(f"  持仓 {i + 1}: {market} | {side} | {size}")

                except Exception as e:
                    print(f"  解析第 {i + 1} 行失败: {e}")
                    continue

            print(f"✓ 共找到 {len(positions)} 个持仓")
            return positions

        except Exception as e:
            print(f"✗ 获取持仓失败: {e}")
            return []

    async def close_position_market(self, market: str = None, row_index: int = None) -> bool:
        """
        使用市价单平仓

        Args:
            market: 市场名称，如 "ETH-USD-PERP"
            row_index: 持仓在表格中的行索引（从0开始）

        Returns:
            bool: 操作是否成功
        """
        try:
            print("\n" + "=" * 60)
            print(f"开始市价平仓: {market if market else f'第{row_index + 1}个持仓'}")
            print("=" * 60)

            positions_tab = self.page.locator(
                'button[role="tab"]:has-text("位置")'
            ).first

            if await positions_tab.get_attribute('aria-selected') != 'true':
                await positions_tab.click()
                await asyncio.sleep(1)

            positions_panel = self.page.locator(
                'div[role="tabpanel"][id="open-positions"]'
            )

            await expect(positions_panel).to_be_visible(timeout=5000)

            table_rows = positions_panel.locator('tbody tr')
            target_row = None

            if row_index is not None:
                if row_index < await table_rows.count():
                    target_row = table_rows.nth(row_index)
                else:
                    print(f"✗ 索引 {row_index} 超出范围")
                    return False
            elif market:
                for i in range(await table_rows.count()):
                    row = table_rows.nth(i)
                    market_link = row.locator('a').first
                    row_market = (await market_link.text_content()).strip()

                    if market in row_market:
                        target_row = row
                        print(f"✓ 找到市场 {market} 的持仓")
                        break

                if target_row is None:
                    print(f"✗ 未找到市场 {market} 的持仓")
                    return False
            else:
                print("✗ 必须指定 market 或 row_index")
                return False

            close_buttons = target_row.locator('button:has-text("市场")')

            if await close_buttons.count() == 0:
                print("✗ 未找到市场平仓按钮")
                return False

            market_close_button = close_buttons.last

            await expect(market_close_button).to_be_visible(timeout=5000)
            await expect(market_close_button).to_be_enabled(timeout=5000)

            await market_close_button.scroll_into_view_if_needed()
            await asyncio.sleep(0.3)

            await market_close_button.click()
            print("✓ 已点击市场平仓按钮")

            await asyncio.sleep(1)

            # 等待弹窗出现
            print("等待平仓确认弹窗...")

            modal_title = self.page.locator('h1:has-text("市场关闭")')

            if await modal_title.count() > 0 and await modal_title.is_visible():
                print("✓ 平仓确认弹窗已出现")

                try:
                    action_div = self.page.locator('div.MarketCloseModal__Action-sc-10otwkl-5').first
                    if await action_div.is_visible():
                        action_text = (await action_div.text_content()).strip()
                        print(f"  操作类型: {action_text}")
                except:
                    pass

                confirm_button_selectors = [
                    'button[type="submit"]:has-text("平多仓")',
                    'button[type="submit"]:has-text("平空仓")',
                    'button[type="submit"].MarketCloseModal__SubmitButton-sc-10otwkl-2',
                    'button.OrderButton-ij10a5-0[type="submit"]'
                ]

                confirm_button = None

                for selector in confirm_button_selectors:
                    btn = self.page.locator(selector)
                    if await btn.count() > 0 and await btn.is_visible():
                        confirm_button = btn.first
                        break

                if confirm_button is None:
                    print("✗ 未找到确认按钮")
                    return False

                await expect(confirm_button).to_be_visible(timeout=5000)
                await expect(confirm_button).to_be_enabled(timeout=5000)

                button_text = (await confirm_button.text_content()).strip()
                print(f"✓ 找到确认按钮: {button_text}")

                await confirm_button.click()
                print(f"✓ 已点击 {button_text} 按钮")

                await asyncio.sleep(1.5)

                if not await modal_title.is_visible():
                    print("✓ 弹窗已关闭，平仓操作已提交")
            else:
                print("⚠️  未检测到平仓确认弹窗，可能已直接提交")

            print("=" * 60)
            print("✅ 市价平仓操作完成")
            print("=" * 60 + "\n")

            return True

        except Exception as e:
            print(f"✗ 市价平仓失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def close_all_positions_market(self) -> bool:
        """
        使用市价单关闭所有持仓

        Returns:
            bool: 操作是否成功
        """
        try:
            print("\n" + "=" * 60)
            print("开始关闭所有持仓")
            print("=" * 60)

            positions = await self.get_current_positions()

            if len(positions) == 0:
                print("✓ 当前无持仓需要关闭")
                return True

            print(f"\n准备关闭 {len(positions)} 个持仓")

            success_count = 0
            fail_count = 0

            for i in range(len(positions) - 1, -1, -1):
                position = positions[i]
                print(f"\n关闭持仓 {i + 1}/{len(positions)}: {position['market']}")

                if await self.close_position_market(row_index=i):
                    success_count += 1
                    await asyncio.sleep(1)
                else:
                    fail_count += 1

            print("\n" + "=" * 60)
            print(f"关闭完成: 成功 {success_count}, 失败 {fail_count}")
            print("=" * 60 + "\n")

            return fail_count == 0

        except Exception as e:
            print(f"✗ 批量平仓失败: {e}")
            return False

    async def verify_position_closed(self, market: str, timeout: int = 10) -> bool:
        """
        验证持仓是否已关闭

        Args:
            market: 市场名称
            timeout: 超时时间（秒）

        Returns:
            bool: 持仓是否已关闭
        """
        try:
            print(f"\n验证 {market} 持仓是否关闭...")

            import time
            end_time = time.time() + timeout

            while time.time() < end_time:
                positions = await self.get_current_positions()

                found = False
                for pos in positions:
                    if market in pos['market']:
                        found = True
                        break

                if not found:
                    print(f"✓ {market} 持仓已关闭")
                    return True

                print(f"  等待持仓关闭... ({int(end_time - time.time())}秒剩余)")
                await asyncio.sleep(1)

            print(f"✗ 超时：{market} 持仓仍存在")
            return False

        except Exception as e:
            print(f"✗ 验证失败: {e}")
            return False

    async def execute_market_order(self, side: str = "BUY", order_size: float = 0.02, verify: bool = True) -> bool:
        """
        执行市价订单流程

        Args:
            side: "BUY" 做多 或 "SELL" 做空
            order_size: 订单大小，默认 0.02
            verify: 是否验证订单成功

        Returns:
            bool: 操作是否成功
        """
        print(1)
        side_text = "做多" if side.upper() == "BUY" else "做空"
        print(2)
        print("\n" + "=" * 60)
        print(f"开始执行市价订单 ({side_text})")
        print("=" * 60)
        print(3)
        if not await self.click_market_order_tab():
            print("❌ 切换市价订单失败，终止操作")
            return False

        await asyncio.sleep(0.5)
        print(4)
        if not await self.set_order_side(side):
            print("❌ 设置订单方向失败，终止操作")
            return False

        await asyncio.sleep(0.3)
        print(5)
        if not await self.input_order_size(order_size):
            print("❌ 输入订单大小失败，终止操作")
            return False

        await asyncio.sleep(0.5)

        if not await self.click_confirm_order(side):
            print("❌ 点击确认按钮失败，终止操作")
            return False

        if verify:
            print("\n" + "-" * 60)
            print("验证订单状态")
            print("-" * 60)

            if await self.verify_order_in_positions(timeout=5):
                print("=" * 60)
                print(f"✅ 市价{side_text}订单执行并成交成功")
                print("=" * 60 + "\n")
                return True

            if await self.wait_for_order_confirmation(timeout=5):
                print("=" * 60)
                print(f"✅ 市价{side_text}订单已提交（等待成交）")
                print("=" * 60 + "\n")
                return True

            print("=" * 60)
            print("❌ 未能确认订单状态")
            print("=" * 60 + "\n")
            return False

        print("=" * 60)
        print(f"✅ 市价{side_text}订单提交完成（未验证）")
        print("=" * 60 + "\n")
        return True

    async def execute_limit_order(self, side: str = "BUY", order_size: float = 0.02, verify: bool = True) -> bool:
        """
        执行完整的限价订单流程

        Args:
            side: "BUY" 做多 或 "SELL" 做空
            order_size: 订单大小，默认 0.02
            verify: 是否验证订单成功

        Returns:
            bool: 操作是否成功
        """
        side_text = "做多" if side.upper() == "BUY" else "做空"

        print("\n" + "=" * 60)
        print(f"开始执行限价订单 ({side_text})")
        print("=" * 60)

        bid = await self.get_highest_bid_price()
        ask = await self.get_lowest_ask_price()

        if bid is None or ask is None:
            print("❌ 无法获取有效价格，终止操作")
            return False

        if ask <= bid:
            print(f"❌ 价格异常：卖价({ask}) <= 买价({bid})，终止操作")
            return False

        mid_price = self.calculate_mid_price(bid, ask)

        if not await self.click_limit_order_tab():
            print("❌ 切换限价订单失败，终止操作")
            return False

        await asyncio.sleep(0.5)

        if not await self.set_order_side(side):
            print("❌ 设置订单方向失败，终止操作")
            return False

        await asyncio.sleep(0.3)

        if not await self.input_limit_price(mid_price):
            print("❌ 输入限价失败，终止操作")
            return False

        await asyncio.sleep(0.3)

        if not await self.input_order_size(order_size):
            print("❌ 输入订单大小失败，终止操作")
            return False

        await asyncio.sleep(0.5)

        if not await self.click_confirm_order(side):
            print("❌ 点击确认按钮失败，终止操作")
            return False

        if verify:
            print("\n" + "-" * 60)
            print("验证订单状态")
            print("-" * 60)

            if await self.wait_for_order_confirmation(timeout=10):
                print("=" * 60)
                print(f"✅ 限价{side_text}订单提交成功")
                print("=" * 60 + "\n")
                return True

            if await self.verify_order_in_positions(timeout=3):
                print("=" * 60)
                print(f"✅ 限价{side_text}订单已成交")
                print("=" * 60 + "\n")
                return True

            print("=" * 60)
            print("❌ 未能确认订单状态")
            print("=" * 60 + "\n")
            return False

        print("=" * 60)
        print(f"✅ 限价{side_text}订单提交完成（未验证）")
        print("=" * 60 + "\n")
        return True



