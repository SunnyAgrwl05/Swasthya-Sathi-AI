import "@testing-library/jest-dom";

// jsdom does not implement scrollIntoView; stub it globally so ChatAgent tests
// don't throw "scrollIntoView is not a function" on the bottomRef effect.
window.HTMLElement.prototype.scrollIntoView = vi.fn();
