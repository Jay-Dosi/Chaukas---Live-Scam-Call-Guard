import { forwardRef } from 'react';

export interface TableProps extends React.TableHTMLAttributes<HTMLTableElement> {
  compact?: boolean;
}

export const Table = forwardRef<HTMLTableElement, TableProps>(
  ({ className = '', compact = false, children, ...rest }, ref) => {
    const classes = ['table', compact && 'table--compact', className].filter(Boolean).join(' ');
    return <table ref={ref} className={classes} {...rest}>{children}</table>;
  }
);

Table.displayName = 'Table';

export const Thead = forwardRef<HTMLTableSectionElement, React.ThHTMLAttributes<HTMLTableSectionElement>>(
  ({ className = '', children, ...rest }, ref) => (
    <thead ref={ref} className={className} {...rest}>{children}</thead>
  )
);
Thead.displayName = 'Thead';

export const Tbody = forwardRef<HTMLTableSectionElement, React.ThHTMLAttributes<HTMLTableSectionElement>>(
  ({ className = '', children, ...rest }, ref) => (
    <tbody ref={ref} className={className} {...rest}>{children}</tbody>
  )
);
Tbody.displayName = 'Tbody';

export const Tr = forwardRef<HTMLTableRowElement, React.ThHTMLAttributes<HTMLTableRowElement>>(
  ({ className = '', children, ...rest }, ref) => (
    <tr ref={ref} className={className} {...rest}>{children}</tr>
  )
);
Tr.displayName = 'Tr';

export const Th = forwardRef<HTMLTableCellElement, React.ThHTMLAttributes<HTMLTableCellElement>>(
  ({ className = '', children, ...rest }, ref) => (
    <th ref={ref} className={className} {...rest}>{children}</th>
  )
);
Th.displayName = 'Th';

export const Td = forwardRef<HTMLTableCellElement, React.TdHTMLAttributes<HTMLTableCellElement>>(
  ({ className = '', children, ...rest }, ref) => (
    <td ref={ref} className={className} {...rest}>{children}</td>
  )
);
Td.displayName = 'Td';