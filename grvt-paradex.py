# hedge_trading.py
# -*- coding: utf-8 -*-
"""
GRVT 和 Paradex 对冲交易机器人
自动监控两个平台的价格差异，执行套利交易
"""

import asyncio
from playwright.async_api import async_playwright, Page as AsyncPage
from grvt import GrvtTradingBot
from paradex_trader import  ParadexTrader
from typing import Optional, Tuple
from datetime import datetime
import random



class HedgeTradingBot:
    """对冲交易机器人"""

    def __init__(
            self,
            grvt_page: AsyncPage,
            paradex_page: AsyncPage,
            price_diff_threshold: float = 10.0,
            order_size: float = 0.002,
            check_interval: int = 5,
    ):
        self.grvt_bot = GrvtTradingBot(grvt_page)
        self.paradex_trader = ParadexTrader(paradex_page)

        self.price_diff_threshold = price_diff_threshold
        self.order_size = order_size
        self.check_interval = check_interval

        self.is_running = False
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0

    async def get_grvt_mid_price(self) -> Optional[float]:
        """获取GRVT的中间价"""
        try:
            bid, ask = await self.grvt_bot.get_orderbook_prices()
            if bid and ask:
                return (bid + ask) / 2
            return None
        except Exception as e:
            print(f"❌ 获取GRVT价格失败: {e}")
            return None

    async def get_paradex_mid_price(self) -> Optional[float]:
        """获取Paradex的中间价"""
        try:
            bid = await self.paradex_trader.get_highest_bid_price()
            ask = await self.paradex_trader.get_lowest_ask_price()

            if bid and ask:
                return (bid + ask) / 2
            return None
        except Exception as e:
            print(f"❌ 获取Paradex价格失败: {e}")
            return None

    async def get_price_difference(self) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """获取两个平台的价格差异"""
        try:
            print("\n" + "-" * 60)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取价格信息...")

            # 并行获取两个价格
            grvt_price, paradex_price = await asyncio.gather(
                self.get_grvt_mid_price(),
                self.get_paradex_mid_price()
            )

            if grvt_price is None or paradex_price is None:
                print("❌ 无法获取完整价格信息")
                return None, None, None

            price_diff = grvt_price - paradex_price
            diff_pct = (price_diff / paradex_price) * 100

            print(f"  GRVT 价格:    ${grvt_price:,.2f}")
            print(f"  Paradex 价格: ${paradex_price:,.2f}")
            print(f"  价差:         ${price_diff:+,.2f} ({diff_pct:+.3f}%)")
            print("-" * 60)

            return grvt_price, paradex_price, price_diff

        except Exception as e:
            print(f"❌ 获取价格差异失败: {e}")
            return None, None, None

    async def execute_hedge_grvt_short_paradex_long(self, grvt_price: float) -> bool:
        """
        执行对冲：GRVT开空 + Paradex开多
        """
        try:
            print("\n" + "🔥" * 30)
            print("执行对冲策略：GRVT做空 + Paradex做多")
            print("🔥" * 30)

            # 第一步：在GRVT限价开空
            print("\n[1/3] GRVT 限价开空...")
            if not await self.grvt_bot.limit_sell_short(price=grvt_price, quantity=self.order_size):
                print("❌ GRVT开空失败")
                return False

            print("✅ GRVT限价单已提交")

            # 第二步：等待成交
            print("\n[2/3] 等待GRVT订单成交...")
            max_wait = 10
            for i in range(max_wait):
                await asyncio.sleep(1)
                position_count = await self.grvt_bot.check_positions(show_details=False)

                if position_count > 0:
                    print(f"✅ GRVT订单已成交（等待{i + 1}秒）")

                    break

                if i % 5 == 4:
                    print(f"  等待中... ({i + 1}/{max_wait}秒)")
            else:
                print("⚠️ GRVT订单超时未成交，检查挂单...")
                await self.grvt_bot.cancel_order(row_index=0)
                await self.grvt_bot.check_open_orders(show_details=True)
                return False

            # 第三步：在Paradex市价开多
            print("\n[3/3] Paradex 市价开多...")
            if not await self.paradex_trader.execute_market_order(side="BUY", order_size=self.order_size, verify=True):
                print("❌ Paradex开多失败")
                print("⚠️ 注意：GRVT已有空头持仓，需要手动处理！")
                return False

            print("✅ Paradex市价单已成交")

            await self.grvt_bot.set_position_tpsl(
                position_index=0,
                tp_roi=50,
                sl_roi=-50
            )
            print("✅ GRVT TP SL 设置成功")


            print("\n" + "🎊" * 30)
            print("对冲成功：GRVT空头 + Paradex多头")
            print("🎊" * 30 + "\n")

            return True

        except Exception as e:
            print(f"❌ 对冲执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def execute_hedge_grvt_long_paradex_short(self, grvt_price: float) -> bool:
        """
        执行对冲：GRVT开多 + Paradex开空
        """
        try:
            print("\n" + "🔥" * 30)
            print("执行对冲策略：GRVT做多 + Paradex做空")
            print("🔥" * 30)

            # 第一步：在GRVT限价开多
            print("\n[1/3] GRVT 限价开多...")
            if not await self.grvt_bot.limit_buy_long(price=grvt_price, quantity=self.order_size):
                print("❌ GRVT开多失败")
                return False

            print("✅ GRVT限价单已提交")

            # 第二步：等待成交
            print("\n[2/3] 等待GRVT订单成交...")
            max_wait = 10
            for i in range(max_wait):
                await asyncio.sleep(1)
                position_count = await self.grvt_bot.check_positions(show_details=False)

                if position_count > 0:
                    print(f"✅ GRVT订单已成交（等待{i + 1}秒）")
                    await self.grvt_bot.set_position_tpsl(
                        position_index=0,
                        tp_roi=50,
                        sl_roi=-50
                    )
                    break

                if i % 5 == 4:
                    print(f"  等待中... ({i + 1}/{max_wait}秒)")
            else:
                print("⚠️ GRVT订单超时未成交，检查挂单...")
                await self.grvt_bot.check_open_orders(show_details=True)
                await self.grvt_bot.cancel_order(row_index=0)
                return False

            # 第三步：在Paradex市价开空
            print("\n[3/3] Paradex 市价开空...")
            if not await self.paradex_trader.execute_market_order(side="SELL", order_size=self.order_size):
                print("❌ Paradex开空失败")
                print("⚠️ 注意：GRVT已有多头持仓，需要手动处理！")
                return False

            print("✅ Paradex市价单已成交")

            await self.grvt_bot.set_position_tpsl(
                position_index=0,
                tp_roi=50,
                sl_roi=-50
            )

            print("\n" + "🎊" * 30)
            print("对冲成功：GRVT多头 + Paradex空头")
            print("🎊" * 30 + "\n")

            return True

        except Exception as e:
            print(f"❌ 对冲执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def close_existing_positions(self) -> bool:
        """
        关闭现有的 GRVT 和 Paradex 持仓
        先挂单关闭 GRVT，等待成交后市价关闭 Paradex
        """
        try:
            print("\n" + "🔄" * 30)
            print("检查并关闭现有持仓")
            print("🔄" * 30)

            # 检查 GRVT 持仓
            grvt_positions = await self.grvt_bot.check_positions(show_details=False)
            
            if grvt_positions > 0:
                print(f"\n[1/3] 发现 {grvt_positions} 个 GRVT 持仓，准备限价平仓...")
                
                # 限价平仓第一个 GRVT 持仓
                if not await self.grvt_bot.limit_close_position(0):
                    print("❌ GRVT 限价平仓失败")
                    return False
                
                print("✅ GRVT 限价平仓订单已提交")
                
                # 等待 GRVT 订单成交
                print("\n[2/3] 等待 GRVT 平仓订单成交...")
                max_wait = 30
                for i in range(max_wait):
                    await asyncio.sleep(1)
                    remaining_positions = await self.grvt_bot.check_positions(show_details=False)
                    
                    if remaining_positions == 0:
                        print(f"✅ GRVT 平仓订单已成交（等待 {i + 1} 秒）")
                        break
                    
                    if i % 5 == 4:
                        print(f"  等待中... ({i + 1}/{max_wait} 秒)")
                else:
                    print("⚠️ GRVT 平仓订单超时未成交")
                    # 尝试取消挂单并市价平仓
                    print("  尝试取消挂单并市价平仓...")
                    await self.grvt_bot.cancel_order(row_index=0)
                    await asyncio.sleep(1)
                    if not await self.grvt_bot.market_close_position(0):
                        print("❌ GRVT 市价平仓也失败")
                        return False
                    await asyncio.sleep(2)
            else:
                print("✅ GRVT 无持仓需要关闭")
            
            # 检查并关闭 Paradex 持仓
            paradex_positions = await self.paradex_trader.get_current_positions()
            
            if len(paradex_positions) > 0:
                print(f"\n[3/3] 发现 {len(paradex_positions)} 个 Paradex 持仓，准备市价平仓...")
                
                # 市价平仓所有 Paradex 持仓
                if not await self.paradex_trader.close_all_positions_market():
                    print("❌ Paradex 市价平仓失败")
                    return False
                
                print("✅ Paradex 持仓已全部平仓")
                await asyncio.sleep(2)
            else:
                print("✅ Paradex 无持仓需要关闭")
            
            print("\n" + "✅" * 30)
            print("所有持仓已关闭")
            print("✅" * 30 + "\n")
            
            return True
            
        except Exception as e:
            print(f"❌ 关闭持仓失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def check_and_execute_hedge(self) -> bool:
        """检查价格并执行对冲"""
        try:
            # 获取价格并执行对冲
            grvt_price, paradex_price, price_diff = await self.get_price_difference()

            if grvt_price is None or paradex_price is None or price_diff is None:
                return False

            abs_diff = abs(price_diff)

            if abs_diff < self.price_diff_threshold:
                print(f"ℹ️  价差 ${abs_diff:.2f} 小于阈值 ${self.price_diff_threshold:.2f}，不交易")
                return False

            self.total_trades += 1

            # 执行开仓
            if price_diff > 0:
                print(f"\n💰 发现套利机会：GRVT价格高 ${abs_diff:.2f}")
                success = await self.execute_hedge_grvt_short_paradex_long(grvt_price)
            else:
                print(f"\n💰 发现套利机会：GRVT价格低 ${abs_diff:.2f}")
                success = await self.execute_hedge_grvt_long_paradex_short(grvt_price)

            if not success:
                self.failed_trades += 1
                return False
            
            self.successful_trades += 1
            
            # 开仓成功后，关闭持仓
            print("\n" + "=" * 60)
            print("步骤 2: 关闭持仓")
            print("=" * 60)
            
            if not await self.close_existing_positions():
                print("❌ 关闭持仓失败")
                return False
            
            # 随机等待 3-5 分钟后继续下一次
            wait_time = random.randint(180, 300)  # 180-300 秒 = 3-5 分钟
            print(f"\n⏳ 随机等待 {wait_time} 秒 ({wait_time/60:.1f} 分钟) 后继续下一次交易...")
            await asyncio.sleep(wait_time)

            return True

        except Exception as e:
            print(f"❌ 检查和执行对冲失败: {e}")
            return False

    async def start_monitoring(self):
        """开始监控价格并自动执行对冲"""
        try:
            self.is_running = True

            print("\n" + "=" * 60)
            print("🤖 对冲交易机器人已启动")
            print("=" * 60)
            print(f"  价差阈值: ${self.price_diff_threshold:.2f}")
            print(f"  订单大小: {self.order_size}")
            print(f"  检查间隔: {self.check_interval}秒")
            print("=" * 60)

            print("\n按 Ctrl+C 停止监控\n")

            while self.is_running:
                try:
                    await self.check_and_execute_hedge()
                    print(f"\n⏳ 等待 {self.check_interval} 秒后继续监控...\n")
                    await asyncio.sleep(self.check_interval)

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(f"❌ 循环中发生错误: {e}")
                    await asyncio.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n收到停止信号...")
            self.is_running = False
        finally:
            self.print_statistics()

    def print_statistics(self):
        """打印交易统计"""
        print("\n" + "=" * 60)
        print("📊 交易统计")
        print("=" * 60)
        print(f"  总交易次数: {self.total_trades}")
        print(f"  成功: {self.successful_trades}")
        print(f"  失败: {self.failed_trades}")
        if self.total_trades > 0:
            success_rate = (self.successful_trades / self.total_trades) * 100
            print(f"  成功率: {success_rate:.1f}%")
        print("=" * 60 + "\n")


# ==================== 浏览器配置 ====================

async def create_browser_context(playwright):
    """创建浏览器上下文"""
    workid = 44
    proxy = "127.0.0.1:7890" # if workid == 44 else f"127.0.0.1:400{workid}"
    user_data = r"D:\"
    path_to_extension = r"D:\"
    path_to_extension2 = r"0"

    browser = await playwright.chromium.launch_persistent_context(
        user_data_dir=user_data + str(workid),
        executable_path=r"",
        accept_downloads=False,
        headless=False,
        bypass_csp=True,
        slow_mo=10,
        channel="chrome",
        proxy={"server": proxy},
        viewport={'width': 1560, 'height': 960},
        args=[
            f'--worker-id={workid}',
            '--disable-blink-features=AutomationControlled',
            '--remote-debugging-port=9222',
            f"--disable-extensions-except={path_to_extension},{path_to_extension2}",
            f"--load-extension={path_to_extension},{path_to_extension2}",
            '--start-maximized',
        ]
    )
    return browser


# ==================== 主程序 ====================

async def main():
    """主程序"""
    print("=" * 60)
    print("GRVT vs Paradex 对冲交易机器人")
    print("=" * 60)
    print("1. 单次对冲交易（手动）")
    print("2. 自动监控并对冲")
    print("3. 仅查看价格差异")
    print("=" * 60)

    choice = input("\n请选择模式 (1-3): ").strip()

    # 创建浏览器（只创建一个）
    async with async_playwright() as playwright:
        print("\n正在启动浏览器...")

        # 创建一个浏览器上下文
        context = await create_browser_context(playwright)

        # 创建两个标签页
        grvt_page = await context.new_page()
        paradex_page = await context.new_page()

        try:
            # 打开两个交易页面
            print("正在打开GRVT交易页面...")
            await grvt_page.goto("https://testnet.grvt.io/exchange/perpetual/BTC-USDT")
            # await grvt_page.wait_for_load_state("networkidle")

            print("正在打开Paradex交易页面...")
            await paradex_page.goto("https://app.testnet.paradex.trade/trade/BTC-USD-PERP")
            # await paradex_page.wait_for_load_state("networkidle")

            await asyncio.sleep(3)

            # 创建对冲机器人
            if choice == '1':
                # 单次手动对冲
                price_diff_threshold = float(input("请输入价差阈值（美元，默认10）: ").strip() or "10")
                order_size = float(input("请输入订单大小（默认0.002）: ").strip() or "0.002")

                bot = HedgeTradingBot(
                    grvt_page=grvt_page,
                    paradex_page=paradex_page,
                    price_diff_threshold=price_diff_threshold,
                    order_size=order_size
                )

                await bot.check_and_execute_hedge()

            elif choice == '2':
                # 自动监控
                price_diff_threshold = float(input("请输入价差阈值（美元，默认10）: ").strip() or "10")
                order_size = float(input("请输入订单大小（默认0.002）: ").strip() or "0.002")
                check_interval = int(input("请输入检查间隔（秒，默认5）: ").strip() or "5")

                bot = HedgeTradingBot(
                    grvt_page=grvt_page,
                    paradex_page=paradex_page,
                    price_diff_threshold=price_diff_threshold,
                    order_size=order_size,
                    check_interval=check_interval
                )

                await bot.start_monitoring()

            elif choice == '3':
                # 仅查看价格
                bot = HedgeTradingBot(
                    grvt_page=grvt_page,
                    paradex_page=paradex_page
                )

                print("\n监控价格中，按 Ctrl+C 停止...\n")
                try:
                    while True:
                        await bot.get_price_difference()
                        await asyncio.sleep(5)
                except KeyboardInterrupt:
                    print("\n停止监控")

            else:
                print("无效的选择")

            # 保持浏览器打开
            print("\n浏览器将保持打开，按 Ctrl+C 关闭...")
            await asyncio.sleep(3600)

        except KeyboardInterrupt:
            print("\n收到中断信号，正在关闭...")
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(main())