import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from 'react'
import { ArrowUpRight, Info } from 'lucide-react'
import { Link } from 'react-router-dom'

export function Button({ variant = 'primary', className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' }) {
  return <button className={`button button--${variant} ${className}`} {...props} />
}
export function ActionLink({ to, children, secondary = false }: { to: string; children: ReactNode; secondary?: boolean }) {
  return <Link className={`button button--${secondary ? 'secondary' : 'primary'}`} to={to}>{children}<ArrowUpRight size={17} aria-hidden="true" /></Link>
}
export function Panel({ className = '', ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={`panel ${className}`} {...props} /> }
export function Notice({ children, error = false }: { children: ReactNode; error?: boolean }) {
  return <div className="notice" role={error ? 'alert' : 'status'}><Info size={18} aria-hidden="true" /><div>{children}</div></div>
}
export function Eyebrow({ children }: { children: ReactNode }) { return <p className="eyebrow">{children}</p> }
