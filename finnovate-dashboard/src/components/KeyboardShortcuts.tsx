import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const KeyboardShortcuts = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only trigger shortcuts when not in input fields
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }

      // Ctrl/Cmd + key combinations
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 'n':
            event.preventDefault();
            navigate('/invoices/create');
            toast.success('Creating new invoice...');
            break;
          case 'h':
            event.preventDefault();
            navigate('/');
            toast.success('Navigating to dashboard...');
            break;
          case 'i':
            event.preventDefault();
            navigate('/invoices');
            toast.success('Navigating to invoices...');
            break;
          case 'c':
            event.preventDefault();
            navigate('/customers');
            toast.success('Navigating to customers...');
            break;
          case 'o':
            event.preventDefault();
            navigate('/overdue');
            toast.success('Navigating to overdue management...');
            break;
          case '/':
            event.preventDefault();
            showShortcutsHelp();
            break;
        }
      }
    };

    const showShortcutsHelp = () => {
      toast(
        'Keyboard Shortcuts:\n' +
        'Ctrl+N: New Invoice\n' +
        'Ctrl+H: Dashboard\n' +
        'Ctrl+I: Invoices\n' +
        'Ctrl+C: Customers\n' +
        'Ctrl+O: Overdue\n' +
        'Ctrl+/: Show this help',
        {
          duration: 6000,
          style: {
            whiteSpace: 'pre-line',
            textAlign: 'left',
          },
        }
      );
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [navigate]);

  return null;
};

export default KeyboardShortcuts;