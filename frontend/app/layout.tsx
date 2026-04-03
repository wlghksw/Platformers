import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Blog Auto Poster",
  description: "AI-Powered Blog Content Generator",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>
        <div className="layout">
          <aside className="sidebar">
            <div className="logo">
              <span style={{ fontSize: '24px' }}>📝</span>
              <span>Blog Auto</span>
            </div>
            
            <nav className="nav-menu">
              <ul>
                <li className="nav-item active">
                  <span>🏠</span> Dashboard
                </li>
                <li className="nav-item">
                  <span>📅</span> History
                </li>
                <li className="nav-item">
                  <span>⚙️</span> Settings
                </li>
              </ul>
            </nav>
            
            <div className="nav-item" style={{ marginTop: 'auto' }}>
              <span>🚪</span> Logout
            </div>
          </aside>
          
          <main className="main">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
