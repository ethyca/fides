import { render, screen } from '../../../../__tests__/test-utils';
import ProtectedRoute from '../ProtectedRoute';

const useRouter = jest.spyOn(require('next/router'), 'useRouter');

const preloadedLoginState = {
  auth: {
    user: {
      username: 'Test',
    },
    token: 'Valid Token',
  },
};

describe('ProtectedRoute', () => {
  describe('when user is not logged in', () => {
    it('should render provided fallback component before redirecting', () => {
      useRouter.mockImplementationOnce(() => ({
        push: () => {},
      }));
      render(
        <ProtectedRoute authenticatedBlock={<div>Not Authorized</div>}>
          <div>Protected Page</div>
        </ProtectedRoute>,
        {
          preloadedState: {},
        }
      );

      const unauthorizedMessage = screen.getByText('Not Authorized');
      const protectedContent = screen.queryByText('Protected Page');
      expect(unauthorizedMessage).toBeInTheDocument();
      expect(protectedContent).toBeNull();
    });

    it('should default to redirecting to /login', () => {
      const push = jest.fn();
      useRouter.mockImplementationOnce(() => ({
        push,
      }));

      render(
        <ProtectedRoute>
          <div>Protected Page</div>
        </ProtectedRoute>,
        {
          preloadedState: {},
        }
      );

      expect(push).toHaveBeenCalledWith('/login');
    });

    it('should redirect to specified route', () => {
      const push = jest.fn();
      useRouter.mockImplementationOnce(() => ({
        push,
      }));

      render(
        <ProtectedRoute redirectUrl="some/other/page">
          <div>Protected Page</div>
        </ProtectedRoute>,
        {
          preloadedState: {},
        }
      );

      expect(push).toHaveBeenCalledWith('some/other/page');
    });
  });

  describe('when the user is logged in', () => {
    it('should not redirect', () => {
      const push = jest.fn();
      useRouter.mockImplementationOnce(() => ({
        push,
      }));
      render(
        <ProtectedRoute>
          <div>Protected Page</div>
        </ProtectedRoute>,
        {
          preloadedState: preloadedLoginState,
        }
      );
      expect(push).toBeCalledTimes(0);
    });

    it('should render passed children', () => {
      const push = jest.fn();
      useRouter.mockImplementationOnce(() => ({
        push,
      }));

      render(
        <ProtectedRoute>
          <div>Protected Page</div>
        </ProtectedRoute>,
        {
          preloadedState: preloadedLoginState,
        }
      );

      const protectedContent = screen.getByText('Protected Page');
      expect(protectedContent).toBeInTheDocument();
    });
  });
});
