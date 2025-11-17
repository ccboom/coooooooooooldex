"""
GRVT 交易机器人测试和交互界面
"""

import asyncio
from playwright.async_api import async_playwright
from grvt import GrvtTradingBot


# ==================== 浏览器配置 ====================

async def create_browser_context(playwright):
    """创建浏览器上下文"""
    workid = 44
    proxy = "127.0.0.1:400" + str(workid)
    if workid == 44:
        proxy = '127.0.0.1:7890'
    password = ""
    work_args = "--worker-id=" + str(workid)
    user_data = r"D:\1lumao\Workers\\"
    path_to_extension = r"D:\1lumao\metama\12.5.0_0"
    path_to_extension2 = r"D:\1lumao\scamsniffer\0.0.60_0"

    browser = await playwright.chromium.launch_persistent_context(
        # 指定本机用户缓存地址
        user_data_dir=user_data + str(workid),
        # 指定本机google客户端exe的路径
        executable_path=r"C:\Users\中\AppData\Local\VirtualBrowser\Application\VirtualBrowser.exe",
        # 要想通过这个下载文件这个必然要开  默认是False
        accept_downloads=False,
        # 设置不是无头模式
        headless=False,
        bypass_csp=True,
        slow_mo=10,
        channel="chrome",
        proxy={"server": proxy},
        # 设置高分辨率
        viewport={'width': 1500, 'height': 800},
        # screen_size={'width': 1920, 'height': 1080},
        # 跳过检测
        args=[work_args
            , '--disable-blink-features=AutomationControlled', '--remote-debugging-port=9222',
              f"--disable-extensions-except={path_to_extension},{path_to_extension2}",  # 插件地址
              f"--load-extension={path_to_extension},{path_to_extension2}",  # 载入插件
              '--start-maximized',  # 启动时最大化窗口
              '--window-size=1920,1080',  # 设置窗口尺寸
              ]
    )

    return browser


# ==================== 交互式菜单 ====================

async def interactive_terminal():
    """交互式交易终端"""
    async with async_playwright() as playwright:
        context = await create_browser_context(playwright)

        try:
            # 创建交易页面
            page = await context.new_page()
            print("正在打开交易页面...")
            await page.goto("https://testnet.grvt.io/exchange/perpetual/BTC-USDT")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            # 创建交易机器人
            bot = GrvtTradingBot(page)

            while True:
                print("\n" + "=" * 60)
                print("GRVT 交易终端")
                print("=" * 60)
                print("\n【开仓操作】")
                print("1. 市价做多")
                print("2. 市价做空")
                print("3. 限价做多")
                print("4. 限价做空")
                print("\n【平仓操作】")
                print("5. 查看当前持仓")
                print("6. 市价平仓（第一个持仓）")
                print("7. 市价平仓（选择持仓）")
                print("8. 市价平仓所有持仓")
                print("9. 限价平仓（第一个持仓）")
                print("10. 限价平仓（选择持仓）")
                print("\n【设置】")
                print("11. 查看当前杠杆")
                print("12. 修改杠杆倍数")
                print("\n【其他】")
                print("13. 检查未结订单")
                print("0. 退出")
                print("=" * 60)

                choice = input("\n请选择操作 (0-13): ").strip()

                if choice == '0':
                    print("退出程序...")
                    break

                elif choice == '1':
                    # 市价做多
                    quantity = input("请输入数量 (默认0.002): ").strip()
                    quantity = float(quantity) if quantity else 0.002
                    await bot.market_buy_long(quantity)

                elif choice == '2':
                    # 市价做空
                    quantity = input("请输入数量 (默认0.002): ").strip()
                    quantity = float(quantity) if quantity else 0.002
                    await bot.market_sell_short(quantity)

                elif choice == '3':
                    # 限价做多
                    price = input("请输入价格 (留空使用中间价): ").strip()
                    price = float(price) if price else None
                    quantity = input("请输入数量 (默认0.002): ").strip()
                    quantity = float(quantity) if quantity else 0.002
                    await bot.limit_buy_long(price, quantity)

                elif choice == '4':
                    # 限价做空
                    price = input("请输入价格 (留空使用中间价): ").strip()
                    price = float(price) if price else None
                    quantity = input("请输入数量 (默认0.002): ").strip()
                    quantity = float(quantity) if quantity else 0.002
                    await bot.limit_sell_short(price, quantity)

                elif choice == '5':
                    # 查看持仓
                    await bot.check_positions(show_details=True)

                elif choice == '6':
                    # 市价平仓第一个持仓
                    await bot.market_close_position(0)

                elif choice == '7':
                    # 市价平仓选择的持仓
                    positions = await bot.get_position_list()
                    if positions:
                        print("\n当前持仓:")
                        for i, pos in enumerate(positions):
                            print(f"{i}. {pos['product']} - {pos['quantity']}")

                        index = input("\n请选择要平仓的持仓索引: ").strip()
                        try:
                            index = int(index)
                            await bot.market_close_position(index)
                        except:
                            print("❌ 无效的索引")
                    else:
                        print("❌ 没有持仓")

                elif choice == '8':
                    # 市价平仓所有持仓
                    confirm = input("确认要平仓所有持仓吗？(y/n): ").strip().lower()
                    if confirm == 'y':
                        await bot.close_all_positions_market()

                elif choice == '9':
                    # 限价平仓第一个持仓
                    price = input("请输入价格 (留空使用中间价): ").strip()
                    price = float(price) if price else None
                    await bot.limit_close_position(0, price)

                elif choice == '10':
                    # 限价平仓选择的持仓
                    positions = await bot.get_position_list()
                    if positions:
                        print("\n当前持仓:")
                        for i, pos in enumerate(positions):
                            print(f"{i}. {pos['product']} - {pos['quantity']}")

                        index = input("\n请选择要平仓的持仓索引: ").strip()
                        try:
                            index = int(index)
                            price = input("请输入价格 (留空使用中间价): ").strip()
                            price = float(price) if price else None
                            await bot.limit_close_position(index, price)
                        except:
                            print("❌ 无效的输入")
                    else:
                        print("❌ 没有持仓")

                elif choice == '11':
                    # 查看当前杠杆
                    await bot.get_current_leverage()

                elif choice == '12':
                    # 修改杠杆倍数
                    leverage = input("请输入目标杠杆倍数 (1-50): ").strip()
                    try:
                        leverage = int(leverage)
                        if 1 <= leverage <= 50:
                            await bot.set_leverage(leverage)
                        else:
                            print("❌ 杠杆倍数必须在 1-50 之间")
                    except:
                        print("❌ 无效的杠杆值")

                elif choice == '13':
                    # 检查未结订单
                    await bot.check_open_orders(show_details=True)

                else:
                    print("❌ 无效的选择")

                input("\n按回车继续...")

        except KeyboardInterrupt:
            print("\n收到中断信号，正在关闭...")
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await context.close()


# ==================== 自动化测试 ====================

async def test_full_cycle():
    """测试完整的开仓-平仓流程"""
    async with async_playwright() as playwright:
        context = await create_browser_context(playwright)

        try:
            page = await context.new_page()
            print("正在打开交易页面...")
            await page.goto("https://testnet.grvt.io/exchange/perpetual/BTC-USDT")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            bot = GrvtTradingBot(page)

            # 第一步：限价开仓
            print("\n" + "🔥" * 30)
            print("第一阶段：限价开仓")
            print("🔥" * 30 + "\n")

            if await bot.limit_buy_long(quantity=0.002):
                print("✅ 开仓成功")
            else:
                print("❌ 开仓失败")
                return

            # 等待并检查持仓
            await asyncio.sleep(5)
            position_count = await bot.check_positions()

            if position_count == 0:
                print("⚠️ 订单可能未成交，检查挂单...")
                await bot.check_open_orders()
                return

            # 第二步：等待一段时间
            print("\n⏳ 等待 10 秒后进行平仓...")
            await asyncio.sleep(10)

            # 第三步：限价平仓
            print("\n" + "🔥" * 30)
            print("第二阶段：限价平仓")
            print("🔥" * 30 + "\n")

            if await bot.limit_close_position(0):
                print("✅ 平仓订单已提交")
            else:
                print("❌ 平仓失败")
                return

            # 验证
            await asyncio.sleep(5)
            final_position_count = await bot.check_positions()

            if final_position_count == 0:
                print("\n🎊 测试完成！所有持仓已平仓")
            else:
                print("\n⚠️ 仍有持仓，可能是限价单未成交")
                await bot.check_open_orders()

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


async def test_market_orders():
    """测试市价单"""
    async with async_playwright() as playwright:
        context = await create_browser_context(playwright)

        try:
            page = await context.new_page()
            print("正在打开交易页面...")
            await page.goto("https://testnet.grvt.io/exchange/perpetual/BTC-USDT")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            bot = GrvtTradingBot(page)

            # 市价做多
            print("\n测试市价做多...")
            await bot.market_buy_long(0.002)
            await asyncio.sleep(3)
            await bot.check_positions()

            # 等待
            await asyncio.sleep(10)

            # 市价平仓
            print("\n测试市价平仓...")
            await bot.market_close_position(0)
            await asyncio.sleep(3)
            await bot.check_positions()

            print("\n测试完成！")
            await asyncio.sleep(10)

        finally:
            await context.close()


async def test_leverage():
    """测试杠杆设置"""
    async with async_playwright() as playwright:
        context = await create_browser_context(playwright)

        try:
            page = await context.new_page()
            print("正在打开交易页面...")
            await page.goto("https://testnet.grvt.io/exchange/perpetual/BTC-USDT")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            bot = GrvtTradingBot(page)

            # 查看当前杠杆
            print("\n查看当前杠杆...")
            current = await bot.get_current_leverage()

            # 设置杠杆为 20x
            print("\n设置杠杆为 20x...")
            await bot.set_leverage(20)

            # 验证
            await asyncio.sleep(2)
            new_leverage = await bot.get_current_leverage()

            if new_leverage == 20:
                print("✅ 杠杆设置测试成功")
            else:
                print("❌ 杠杆设置测试失败")

            # 恢复原始杠杆
            if current:
                print(f"\n恢复杠杆为 {current}x...")
                await bot.set_leverage(current)

            await asyncio.sleep(10)

        finally:
            await context.close()


# ==================== 主程序 ====================

if __name__ == "__main__":
    print("GRVT 交易机器人")
    print("=" * 60)
    print("1. 交互式终端")
    print("2. 测试完整流程（限价单）")
    print("3. 测试市价单")
    print("4. 测试杠杆设置")
    print("=" * 60)

    choice = input("请选择模式 (1-4): ").strip()

    if choice == '1':
        asyncio.run(interactive_terminal())
    elif choice == '2':
        asyncio.run(test_full_cycle())
    elif choice == '3':
        asyncio.run(test_market_orders())
    elif choice == '4':
        asyncio.run(test_leverage())
    else:
        print("无效的选择")