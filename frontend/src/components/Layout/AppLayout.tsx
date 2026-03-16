import React, { useState } from 'react';
import { Layout, Menu, Button, Dropdown, Avatar, Badge } from 'antd';
import { BellOutlined, UserOutlined, SettingOutlined, LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import ChatPanel from '../AGUI/ChatPanel';
import styles from './AppLayout.module.css';

const { Header, Sider, Content } = Layout;

interface AppLayoutProps {
  children: React.ReactNode;
  currentMenu?: string;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children, currentMenu = 'dashboard' }) => {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const [theme] = useState<'light' | 'dark'>('dark');

  const handleMenuClick = (key: string) => {
    const routes: Record<string, string> = {
      dashboard: '/',
      documents: '/documents',
      query: '/query',
      operations: '/operations',
      diagnosis: '/diagnosis',
      products: '/products',
    };
    navigate(routes[key]);
  };

  const userMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: '个人资料' },
    { key: 'settings', icon: <SettingOutlined />, label: '设置' },
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出' },
  ];

  const navigationMenu = (
    <Menu
      mode="inline"
      defaultSelectedKeys={[currentMenu]}
      onClick={(e) => handleMenuClick(e.key)}
      className={styles.navigationMenu}
    >
      <Menu.Item key="dashboard" className={styles.menuItem}>
        📊 仪表板
      </Menu.Item>
      <Menu.Item key="documents" className={styles.menuItem}>
        📚 知识库
      </Menu.Item>
      <Menu.Item key="query" className={styles.menuItem}>
        🔍 数据查询
      </Menu.Item>
      <Menu.Item key="operations" className={styles.menuItem}>
        ⚙️ 智能操作
      </Menu.Item>
      <Menu.Item key="diagnosis" className={styles.menuItem}>
        🔬 经营诊断
      </Menu.Item>
      <Menu.Item key="products" className={styles.menuItem}>
        🛍️ 商品管理
      </Menu.Item>
    </Menu>
  );

  return (
    <Layout className={`${styles.appLayout} ${styles[theme]}`}>
      {/* 侧边栏 */}
      <Sider
        width={280}
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        className={styles.sider}
        trigger={null}
      >
        <div className={styles.logo}>
          <span className={styles.logoIcon}>🤖</span>
          {!collapsed && <span className={styles.logoText}>AIGovern</span>}
        </div>
        {navigationMenu}
      </Sider>

      <Layout>
        {/* 顶部导航 */}
        <Header className={styles.header}>
          <div className={styles.headerLeft}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className={styles.collapseBtn}
            />
            <h1 className={styles.pageTitle}>AIGovern Pro</h1>
          </div>

          <div className={styles.headerRight}>
            <Button
              type="text"
              icon={<BellOutlined />}
              className={styles.notificationBtn}
            >
              <Badge count={3} />
            </Button>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Avatar
                icon={<UserOutlined />}
                style={{ cursor: 'pointer', backgroundColor: '#00d9ff' }}
              />
            </Dropdown>
          </div>
        </Header>

        {/* 主内容区 */}
        <Content className={styles.content}>
          {children}
        </Content>
      </Layout>

      {/* 右侧悬浮 ChatPanel */}
      <ChatPanel />
    </Layout>
  );
};

export default AppLayout;
