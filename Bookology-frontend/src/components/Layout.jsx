import React from 'react';
import Header from './Header';
import { Outlet } from 'react-router-dom';

export default function Layout() {
  return (
    <>
      <Header variant="default" />
      <div className="pt-16">
        <Outlet />
      </div>
    </>
  );
}


