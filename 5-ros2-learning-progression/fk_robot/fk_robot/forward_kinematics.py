import rclpy
from rclpy.node import Node

import sympy as sp


class FKNode(Node):

    def __init__(self):

        super().__init__('fk_node')

        self.get_logger().info(
            "Updated Symbolic FK Started"
        )

        # -----------------------------------
        # Better symbolic printing
        # -----------------------------------

        sp.init_printing(use_unicode=True)

        # -----------------------------------
        # Symbolic Variables
        # -----------------------------------

        theta1, theta2, theta3, theta4, theta5 = sp.symbols(
            'theta1 theta2 theta3 theta4 theta5'
        )

        l1, l2, l3, l4, l5, l6 = sp.symbols(
            'l1 l2 l3 l4 l5 l6'
        )

        # -----------------------------------
        # DH MATRICES
        # -----------------------------------

        T01 = self.dh_matrix(
            0,
            0,
            l1,
            theta1
        )

        T12 = self.dh_matrix(
            0,
            -sp.pi/2,
            l2,
            theta2 + sp.pi/2
        )

        T23 = self.dh_matrix(
            l3,
            sp.pi,
            l4,
            theta3 + sp.pi
        )

        T34 = self.dh_matrix(
            l5,
            0,
            0,
            theta4 + sp.pi/2
        )

        T45 = self.dh_matrix(
            0,
            -sp.pi/2,
            -l6,
            theta5
        )

        # -----------------------------------
        # PRINT INDIVIDUAL MATRICES
        # -----------------------------------

        print("\nT01 =")
        sp.pprint(T01)

        print("\nT12 =")
        sp.pprint(T12)

        print("\nT23 =")
        sp.pprint(T23)

        print("\nT34 =")
        sp.pprint(T34)

        print("\nT45 =")
        sp.pprint(T45)

        # -----------------------------------
        # FINAL FK MATRIX
        # -----------------------------------

        T05 = T01 * T12 * T23 * T34 * T45

        # -----------------------------------
        # TRIGONOMETRIC SIMPLIFICATION
        # -----------------------------------

        T05 = sp.trigsimp(T05)

        # -----------------------------------
        # ROTATION MATRIX
        # -----------------------------------

        R05 = T05[0:3, 0:3]

        # -----------------------------------
        # POSITION VECTOR
        # -----------------------------------

        P05 = T05[0:3, 3]

        # -----------------------------------
        # PRINT FINAL RESULTS
        # -----------------------------------

        print("\n==============================")
        print("FINAL TRANSFORMATION MATRIX")
        print("==============================")

        sp.pprint(T05)

        print("\n==============================")
        print("ROTATION MATRIX R05")
        print("==============================")

        sp.pprint(R05)

        print("\n==============================")
        print("POSITION VECTOR P05")
        print("==============================")

        sp.pprint(P05)

    # ------------------------------------------------
    # STANDARD DH MATRIX
    # USING YOUR HANDWRITTEN FORM
    # ------------------------------------------------

    def dh_matrix(self, a, alpha, d, theta):

        T = sp.Matrix([

            [
                sp.cos(theta),
                -sp.sin(theta),
                0,
                a
            ],

            [
                sp.sin(theta) * sp.cos(alpha),
                sp.cos(theta) * sp.cos(alpha),
                -sp.sin(alpha),
                -sp.sin(alpha) * d
            ],

            [
                sp.sin(theta) * sp.sin(alpha),
                sp.cos(theta) * sp.sin(alpha),
                sp.cos(alpha),
                sp.cos(alpha) * d
            ],

            [
                0,
                0,
                0,
                1
            ]

        ])

        return T


def main(args=None):

    rclpy.init(args=args)

    node = FKNode()

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()