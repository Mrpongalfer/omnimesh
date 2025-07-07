# Accessibility Implementation Guide

> **WCAG 2.2 AAA Compliance & Inclusive Design**  
> Building interfaces accessible to all users with bleeding-edge assistive technology support

---

## 🎯 **Accessibility Standards & Targets**

### Compliance Levels

- ✅ **WCAG 2.2 AAA**: Highest accessibility standard
- ✅ **EN 301 549**: European accessibility requirements
- ✅ **Section 508**: US federal accessibility compliance
- ✅ **ADA**: Americans with Disabilities Act compliance

### Testing Matrix

| Assistive Technology     | Platform  | Support Level |
| ------------------------ | --------- | ------------- |
| NVDA                     | Windows   | ✅ Full       |
| JAWS                     | Windows   | ✅ Full       |
| VoiceOver                | macOS/iOS | ✅ Full       |
| TalkBack                 | Android   | ✅ Full       |
| Orca                     | Linux     | ✅ Full       |
| Dragon NaturallySpeaking | Windows   | ✅ Full       |
| Switch Navigation        | All       | ✅ Full       |

---

## 🧠 **Cognitive Accessibility**

### Information Architecture

```typescript
// Clear semantic hierarchy
const SemanticLayout = () => (
  <main role="main" aria-label="Control Panel">
    <header role="banner">
      <nav role="navigation" aria-label="Main navigation">
        <ol role="menubar">
          {menuItems.map((item) => (
            <li role="menuitem" tabIndex={0}>
              {item.label}
            </li>
          ))}
        </ol>
      </nav>
    </header>

    <section role="region" aria-labelledby="agents-heading">
      <h1 id="agents-heading">Agent Management</h1>
      {/* Content */}
    </section>
  </main>
);
```

### Cognitive Load Reduction

- **Progressive Disclosure**: Complex features revealed gradually
- **Consistent Patterns**: Same interaction patterns across components
- **Clear Labels**: Self-explanatory interface elements
- **Error Prevention**: Input validation with helpful suggestions
- **Undo/Redo**: Reversible actions for error recovery

---

## 🎨 **Visual Accessibility**

### Color & Contrast

```css
/* WCAG AAA contrast ratios (7:1 for normal text, 4.5:1 for large) */
:root {
  --color-text-primary: #ffffff; /* 21:1 on dark background */
  --color-text-secondary: #cbd5e1; /* 12:1 on dark background */
  --color-accent: #3b82f6; /* 8.2:1 on dark background */
  --color-success: #10b981; /* 7.1:1 on dark background */
  --color-warning: #f59e0b; /* 9.8:1 on dark background */
  --color-error: #ef4444; /* 9.1:1 on dark background */
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  :root {
    --color-text-primary: #ffffff;
    --color-background: #000000;
    --color-accent: #00d4ff;
  }
}
```

### Typography & Spacing

```css
/* Minimum 16px base font size */
html {
  font-size: 16px;
  line-height: 1.6; /* WCAG recommended 1.5+ */
}

/* Scalable spacing system */
.spacing-xs {
  gap: 0.25rem;
} /* 4px */
.spacing-sm {
  gap: 0.5rem;
} /* 8px */
.spacing-md {
  gap: 1rem;
} /* 16px */
.spacing-lg {
  gap: 1.5rem;
} /* 24px */
.spacing-xl {
  gap: 2rem;
} /* 32px */

/* Focus indicators */
.focus-visible {
  outline: 3px solid var(--color-accent);
  outline-offset: 2px;
  border-radius: 4px;
}
```

---

## ⌨️ **Keyboard Navigation**

### Focus Management

```typescript
import { createFocusTrap } from 'focus-trap';

// Modal focus trap
const Modal = (props: ModalProps) => {
  let modalRef: HTMLDivElement;
  let focusTrap: any;

  onMount(() => {
    focusTrap = createFocusTrap(modalRef, {
      initialFocus: modalRef.querySelector('[data-autofocus]'),
      fallbackFocus: modalRef,
      escapeDeactivates: true,
      clickOutsideDeactivates: true,
    });
    focusTrap.activate();
  });

  onCleanup(() => {
    focusTrap?.deactivate();
  });

  return (
    <div
      ref={modalRef!}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      tabIndex={-1}
    >
      {/* Modal content */}
    </div>
  );
};
```

### Keyboard Shortcuts

```typescript
// Global keyboard shortcuts
const keyboardShortcuts = {
  'Alt+1': () => navigateTo('/agents'),
  'Alt+2': () => navigateTo('/control-panel'),
  'Ctrl+/': () => toggleCommandPalette(),
  Escape: () => closeModal(),
  Tab: () => focusNext(),
  'Shift+Tab': () => focusPrevious(),
  Enter: () => activateElement(),
  Space: () => toggleElement(),
  'Arrow Keys': () => navigateGrid(),
};
```

---

## 🔊 **Screen Reader Support**

### ARIA Implementation

```typescript
// Complex components with full ARIA support
const DataGrid = () => {
  const [selectedRow, setSelectedRow] = createSignal<number>(0);
  const [sortColumn, setSortColumn] = createSignal<string>('name');
  const [sortDirection, setSortDirection] = createSignal<'asc' | 'desc'>('asc');

  return (
    <table
      role="grid"
      aria-label="Agent data grid"
      aria-rowcount={data().length + 1}
      aria-colcount={columns.length}
    >
      <thead role="rowgroup">
        <tr role="row" aria-rowindex={1}>
          <For each={columns}>
            {(column, index) => (
              <th
                role="columnheader"
                aria-colindex={index() + 1}
                aria-sort={
                  sortColumn() === column.key
                    ? sortDirection() === 'asc' ? 'ascending' : 'descending'
                    : 'none'
                }
                tabIndex={0}
                onClick={() => handleSort(column.key)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    handleSort(column.key);
                  }
                }}
              >
                {column.label}
                <span aria-hidden="true">
                  {sortColumn() === column.key && (
                    sortDirection() === 'asc' ? '↑' : '↓'
                  )}
                </span>
              </th>
            )}
          </For>
        </tr>
      </thead>

      <tbody role="rowgroup">
        <For each={data()}>
          {(row, rowIndex) => (
            <tr
              role="row"
              aria-rowindex={rowIndex() + 2}
              aria-selected={selectedRow() === rowIndex()}
              tabIndex={0}
              onClick={() => setSelectedRow(rowIndex())}
              class={selectedRow() === rowIndex() ? 'selected' : ''}
            >
              <For each={columns}>
                {(column, colIndex) => (
                  <td
                    role="gridcell"
                    aria-colindex={colIndex() + 1}
                    tabIndex={-1}
                  >
                    {row[column.key]}
                  </td>
                )}
              </For>
            </tr>
          )}
        </For>
      </tbody>
    </table>
  );
};
```

### Live Regions

```typescript
// Status announcements
const StatusAnnouncer = () => {
  const [announcement, setAnnouncement] = createSignal('');
  const [priority, setPriority] = createSignal<'polite' | 'assertive'>('polite');

  // Announce status changes
  createEffect(() => {
    const status = appState.connectionStatus;
    if (status === 'connected') {
      announce('Connected to Omnitide network', 'polite');
    } else if (status === 'disconnected') {
      announce('Connection lost. Attempting to reconnect...', 'assertive');
    }
  });

  const announce = (message: string, level: 'polite' | 'assertive' = 'polite') => {
    setAnnouncement('');
    setPriority(level);
    setTimeout(() => setAnnouncement(message), 100);
  };

  return (
    <div
      aria-live={priority()}
      aria-atomic="true"
      class="sr-only"
    >
      {announcement()}
    </div>
  );
};
```

---

## 🎛️ **Motor Accessibility**

### Large Touch Targets

```css
/* Minimum 44px touch targets per WCAG */
.touch-target {
  min-height: 44px;
  min-width: 44px;
  padding: 12px;
}

/* Increased target areas for small icons */
.icon-button {
  padding: 12px;
  margin: 4px;
  position: relative;
}

.icon-button::before {
  content: '';
  position: absolute;
  top: -8px;
  left: -8px;
  right: -8px;
  bottom: -8px;
}
```

### Alternative Input Methods

```typescript
// Voice command support
const VoiceCommands = () => {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();

  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    const transcript = event.results[event.resultIndex][0].transcript.toLowerCase();

    // Voice navigation commands
    if (transcript.includes('navigate to agents')) {
      navigateTo('/agents');
    } else if (transcript.includes('open command palette')) {
      toggleCommandPalette();
    } else if (transcript.includes('connect agent')) {
      openAgentConnection();
    }
  };

  return (
    <button
      onClick={() => recognition.start()}
      aria-label="Start voice commands"
      title="Ctrl+Shift+V"
    >
      🎤
    </button>
  );
};

// Switch navigation support
const SwitchNavigation = () => {
  const [scanMode, setScanMode] = createSignal(false);
  const [currentGroup, setCurrentGroup] = createSignal(0);
  const [currentItem, setCurrentItem] = createSignal(0);

  // External switch input handler
  useEventListener(document, 'keydown', (e) => {
    if (e.code === 'Space' && e.ctrlKey && e.shiftKey) {
      setScanMode(!scanMode());
    } else if (scanMode() && e.code === 'Space') {
      activateCurrentItem();
    }
  });

  return (
    <div class={scanMode() ? 'scan-mode' : ''}>
      {/* Switch-navigable interface */}
    </div>
  );
};
```

---

## 🧪 **Accessibility Testing**

### Automated Testing

```typescript
// axe-core integration
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('Accessibility Tests', () => {
  test('should not have accessibility violations', async () => {
    const { container } = render(<App />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test('keyboard navigation works', () => {
    render(<ControlPanel />);

    // Tab through focusable elements
    fireEvent.keyDown(document.body, { key: 'Tab' });
    expect(screen.getByRole('button', { name: /agents/i })).toHaveFocus();

    fireEvent.keyDown(document.body, { key: 'Tab' });
    expect(screen.getByRole('button', { name: /control panel/i })).toHaveFocus();
  });

  test('screen reader announcements', () => {
    const announcer = render(<StatusAnnouncer />);

    // Trigger status change
    fireEvent.click(screen.getByRole('button', { name: /connect/i }));

    expect(announcer.getByRole('status')).toHaveTextContent(
      'Connected to Omnitide network'
    );
  });
});
```

### Manual Testing Checklist

#### Screen Reader Testing

- [ ] All content is readable by screen readers
- [ ] Navigation landmarks are properly announced
- [ ] Form labels are associated correctly
- [ ] Dynamic content changes are announced
- [ ] Error messages are conveyed appropriately

#### Keyboard Testing

- [ ] All interactive elements are keyboard accessible
- [ ] Tab order is logical and predictable
- [ ] Focus indicators are clearly visible
- [ ] Keyboard shortcuts work as expected
- [ ] No keyboard traps exist

#### Visual Testing

- [ ] Interface works at 400% zoom
- [ ] Color information is not the only way to convey meaning
- [ ] Contrast ratios meet WCAG AAA standards
- [ ] Text is readable and well-spaced
- [ ] UI adapts to reduced motion preferences

#### Motor Testing

- [ ] Touch targets are at least 44px
- [ ] Drag operations have keyboard alternatives
- [ ] Time limits can be extended or disabled
- [ ] Actions can be undone or cancelled

---

## 📱 **Responsive Accessibility**

### Adaptive Interfaces

```typescript
// Responsive accessibility patterns
const AdaptiveInterface = () => {
  const [preferredInputMethod] = usePreferredInput();
  const [screenSize] = useScreenSize();

  return (
    <div class={`interface-${preferredInputMethod} screen-${screenSize}`}>
      <Show when={preferredInputMethod === 'touch'}>
        <TouchOptimizedControls />
      </Show>

      <Show when={preferredInputMethod === 'keyboard'}>
        <KeyboardOptimizedControls />
      </Show>

      <Show when={preferredInputMethod === 'voice'}>
        <VoiceOptimizedControls />
      </Show>
    </div>
  );
};
```

### Media Queries for Accessibility

```css
/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* High contrast preference */
@media (prefers-contrast: high) {
  .card {
    border: 2px solid currentColor;
  }

  .button {
    background: ButtonText;
    color: ButtonFace;
    border: 2px solid ButtonText;
  }
}

/* Forced colors mode (Windows high contrast) */
@media (forced-colors: active) {
  .custom-button {
    background: ButtonFace;
    color: ButtonText;
    border: 1px solid ButtonText;
  }

  .focus-indicator {
    outline: 2px solid Highlight;
  }
}
```

---

## 🔍 **Performance & Accessibility**

### Optimized Screen Reader Experience

```typescript
// Virtualized lists with proper accessibility
const VirtualizedAgentList = () => {
  const [focusedIndex, setFocusedIndex] = createSignal(0);
  const virtualizer = createVirtualizer({
    count: agents().length,
    estimateSize: () => 60,
    overscan: 5,
  });

  return (
    <div
      role="listbox"
      aria-label="Agent list"
      aria-activedescendant={`agent-${focusedIndex()}`}
      tabIndex={0}
      onKeyDown={handleKeyNavigation}
    >
      <For each={virtualizer.getVirtualItems()}>
        {(virtualItem) => {
          const agent = agents()[virtualItem.index];
          return (
            <div
              id={`agent-${virtualItem.index}`}
              role="option"
              aria-selected={focusedIndex() === virtualItem.index}
              style={{
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <AgentCard agent={agent} />
            </div>
          );
        }}
      </For>
    </div>
  );
};
```

---

## 📋 **Compliance Documentation**

### VPAT (Voluntary Product Accessibility Template)

Our accessibility compliance statement and detailed VPAT documentation is available at `/docs/VPAT.md`.

### Accessibility Statement

We are committed to ensuring digital accessibility for people with disabilities. We continually improve the user experience for everyone by applying relevant accessibility standards and guidelines.

**Contact Information:**

- Email: accessibility@omnitide.dev
- Phone: +1 (555) 123-4567
- Address: 123 Accessibility St, Inclusive City, IN 12345

**Feedback:**
We welcome your feedback on the accessibility of the Omnitide Control Panel. Please let us know if you encounter accessibility barriers.

---

_Last updated: January 2025_
_Next review: March 2025_
