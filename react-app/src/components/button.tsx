import React, { useState } from "react";
import Alert from "./Alert";
interface Props {
  children: string;
  color?: "primary" | "secondary" | "danger";
  onClick: () => void;
}
const button = ({ children, onClick, color = "primary" }: Props) => {
  return (
    <div>
      <button className={"btn btn-" + color} onClick={onClick}>
        {children}
      </button>
    </div>
  );
};

export default button;
