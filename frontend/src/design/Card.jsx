/** iOS-native Card component */
export default function Card({ children, header, headerRight, icon, iconBg = 'bg-blue-500', className = '', noPad = false, interactive = false }) {
  return (
    <div className={`ios-card ${interactive ? 'ios-card-interactive' : ''} ${className}`}>
      {header && (
        <div className="flex items-center justify-between px-4 pt-4 pb-2">
          <div className="flex items-center gap-3">
            {icon && (
              <div className={`ios-icon ${iconBg} text-white`}>
                <span className="emoji-icon">{icon}</span>
              </div>
            )}
            <span className="ios-headline text-[var(--text-primary)]">{header}</span>
          </div>
          {headerRight && <div>{headerRight}</div>}
        </div>
      )}
      <div className={noPad ? '' : 'px-4 pb-4'}>
        {children}
      </div>
    </div>
  );
}
