import React from 'react';
import Header from './Header';
import { Outlet } from 'react-router-dom';

export default function EditorLayout() {
  return (
    <>
      <Header variant="minimal" />
      <div className="pt-14">
        <Outlet />
      </div>
    </>
  );
}


